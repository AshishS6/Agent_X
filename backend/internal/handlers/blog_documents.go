package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"

	"go-backend/internal/models"
	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

// BlogDocumentsHandler handles blog document-related HTTP requests
type BlogDocumentsHandler struct {
	docRepo   *models.BlogDocumentRepository
	agentRepo *models.AgentRepository
	taskRepo  *models.TaskRepository
	executor  *tools.Executor
}

// NewBlogDocumentsHandler creates a new blog documents handler
func NewBlogDocumentsHandler(executor *tools.Executor) *BlogDocumentsHandler {
	return &BlogDocumentsHandler{
		docRepo:   models.NewBlogDocumentRepository(),
		agentRepo: models.NewAgentRepository(),
		taskRepo:  models.NewTaskRepository(),
		executor:  executor,
	}
}

// CreateDocumentRequest is the request body for creating a blog document
type CreateDocumentRequest struct {
	Brand          string `json:"brand" binding:"required"`
	Topic          string `json:"topic" binding:"required"`
	TargetAudience string `json:"target_audience" binding:"required"`
	Intent         string `json:"intent" binding:"required"`
	CreatedBy      string `json:"created_by"`
}

// Create creates a new blog document
// POST /api/blog/documents
func (h *BlogDocumentsHandler) Create(c *gin.Context) {
	var req CreateDocumentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Validate brand
	brand := models.BlogBrand(req.Brand)
	if brand != models.BlogBrandOPEN && brand != models.BlogBrandZwitch {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid brand. Must be 'OPEN' or 'Zwitch'",
		})
		return
	}

	doc, err := h.docRepo.Create(brand, req.Topic, req.TargetAudience, req.Intent, req.CreatedBy)
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error creating document: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    doc,
	})
}

// GetByID gets a blog document by ID with latest versions
// GET /api/blog/documents/:id
func (h *BlogDocumentsHandler) GetByID(c *gin.Context) {
	id := c.Param("id")

	doc, err := h.docRepo.FindByID(id)
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error fetching document %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if doc == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Document not found",
		})
		return
	}

	// Get latest outline and draft versions
	latestOutline, _ := h.docRepo.GetLatestOutlineVersion(id)
	latestDraft, _ := h.docRepo.GetLatestDraftVersion(id)

	response := gin.H{
		"document": doc,
		"outline":  latestOutline,
		"draft":    latestDraft,
	}

	// Get feedback if versions exist
	if latestOutline != nil {
		feedback, _ := h.docRepo.GetFeedbackForVersion(latestOutline.ID)
		response["outline_feedback"] = feedback
	}
	if latestDraft != nil {
		feedback, _ := h.docRepo.GetFeedbackForVersion(latestDraft.ID)
		response["draft_feedback"] = feedback
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    response,
	})
}

// List lists all blog documents
// GET /api/blog/documents
func (h *BlogDocumentsHandler) List(c *gin.Context) {
	limit := 50
	offset := 0

	if limitStr := c.Query("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 {
			limit = l
		}
	}

	if offsetStr := c.Query("offset"); offsetStr != "" {
		if o, err := strconv.Atoi(offsetStr); err == nil && o >= 0 {
			offset = o
		}
	}

	docs, total, err := h.docRepo.FindAll(limit, offset)
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error listing documents: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    docs,
		"total":   total,
	})
}

// GenerateOutlineRequest is the request body for generating an outline
type GenerateOutlineRequest struct {
	UseRAG bool `json:"use_rag"`
}

// GenerateOutline generates an outline for a document
// POST /api/blog/documents/:id/outlines
func (h *BlogDocumentsHandler) GenerateOutline(c *gin.Context) {
	documentID := c.Param("id")

	// Verify document exists
	doc, err := h.docRepo.FindByID(documentID)
	if err != nil || doc == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Document not found",
		})
		return
	}

	var req GenerateOutlineRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		// Use default if not provided
		req.UseRAG = false
	}

	// Find blog agent
	agent, err := h.agentRepo.FindByType("blog")
	if err != nil || agent == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Blog agent not found",
		})
		return
	}

	// Get next version number
	nextVersion, err := h.docRepo.GetNextOutlineVersion(documentID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Create task for outline generation
	input := map[string]any{
		"document_id":     documentID,
		"brand":           string(doc.Brand),
		"topic":           doc.Topic,
		"target_audience": doc.TargetAudience,
		"intent":          doc.Intent,
		"version":         nextVersion,
		"use_rag":         req.UseRAG,
	}

	task, err := h.taskRepo.Create(agent.ID, "generate_outline_v2", input, "medium", "")
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error creating task: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Execute task asynchronously
	go func() {
		h.taskRepo.UpdateStatus(task.ID, models.TaskStatusProcessing)

		// Local LLM generations (esp. with RAG) can exceed 5 minutes.
		// Use a longer timeout to avoid premature task failures.
		ctx, cancel := context.WithTimeout(context.Background(), 20*60*1000000000) // 20 minutes
		defer cancel()

		tool, exists := tools.GetToolByAgentType(agent.Type)
		if !exists {
			h.taskRepo.UpdateFailed(task.ID, "No CLI tool configured for blog agent")
			return
		}

		cliInput := map[string]any{
			"action":  "generate_outline_v2",
			"task_id": task.ID,
		}
		for k, v := range input {
			cliInput[k] = v
		}

		result, err := h.executor.Execute(ctx, tool, cliInput)
		if err != nil {
			log.Printf("[BlogDocumentsHandler] Task execution error: %v", err)
			h.taskRepo.UpdateFailed(task.ID, err.Error())
			return
		}

		if result.Status == "failed" {
			h.taskRepo.UpdateFailed(task.ID, result.Error)
		} else {
			h.taskRepo.UpdateCompleted(task.ID, result.Output)

			// Save outline to DB from Go (Python subprocess may not have DB access).
			// The Python agent returns the outline structure in result.Output["response"]["structure"].
			if err := h.saveOutlineFromResult(result.Output, documentID, nextVersion); err != nil {
				log.Printf("[BlogDocumentsHandler] Failed to save outline to DB: %v", err)
			}
		}
	}()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    task,
		"message": "Outline generation started",
	})
}

// saveOutlineFromResult parses the executor output and saves the outline structure to the DB.
// The Python agent returns: {"response": {"structure": {"title": "...", "outline": [...]}}}
// This runs in Go so it always has DB access, unlike the Python subprocess.
func (h *BlogDocumentsHandler) saveOutlineFromResult(output map[string]any, documentID string, version int) error {
	if output == nil {
		return fmt.Errorf("output is nil")
	}

	// Navigate output["response"]["structure"]
	response, ok := output["response"].(map[string]any)
	if !ok {
		return fmt.Errorf("output.response is missing or not an object")
	}

	structure, ok := response["structure"].(map[string]any)
	if !ok {
		return fmt.Errorf("output.response.structure is missing or not an object")
	}

	// Marshal structure back to JSON for storage
	structureJSON, err := json.Marshal(structure)
	if err != nil {
		return fmt.Errorf("failed to marshal structure: %w", err)
	}

	_, err = h.docRepo.CreateOutlineVersion(documentID, version, structureJSON, models.BlogVersionStatusDraft)
	if err != nil {
		return fmt.Errorf("failed to create outline version: %w", err)
	}

	log.Printf("[BlogDocumentsHandler] Saved outline version %d for document %s", version, documentID)
	return nil
}

// UpdateOutlineStatusRequest is the request body for updating outline status
type UpdateOutlineStatusRequest struct {
	Status string `json:"status" binding:"required"`
}

// UpdateOutlineStatus updates the status of an outline version
// PUT /api/blog/documents/:id/outlines/:versionId
func (h *BlogDocumentsHandler) UpdateOutlineStatus(c *gin.Context) {
	versionID := c.Param("versionId")

	var req UpdateOutlineStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	status := models.BlogVersionStatus(req.Status)
	if status != models.BlogVersionStatusDraft && status != models.BlogVersionStatusReviewed && status != models.BlogVersionStatusApproved {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid status. Must be 'draft', 'reviewed', or 'approved'",
		})
		return
	}

	err := h.docRepo.UpdateOutlineVersionStatus(versionID, status)
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error updating outline status: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Outline status updated",
	})
}

// UpdateOutlineStructureRequest is the request body for updating outline structure
type UpdateOutlineStructureRequest struct {
	Structure json.RawMessage `json:"structure" binding:"required"`
}

// UpdateOutlineStructure updates the structure of an outline version
// PUT /api/blog/documents/:id/outlines/:versionId/structure
func (h *BlogDocumentsHandler) UpdateOutlineStructure(c *gin.Context) {
	versionID := c.Param("versionId")

	var req UpdateOutlineStructureRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	err := h.docRepo.UpdateOutlineVersionStructure(versionID, req.Structure)
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error updating outline structure: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Outline structure updated",
	})
}

// AddFeedbackRequest is the request body for adding feedback
type AddFeedbackRequest struct {
	TargetType      string  `json:"target_type" binding:"required"` // "outline" or "draft"
	TargetVersionID string  `json:"target_version_id" binding:"required"`
	Scope           string  `json:"scope" binding:"required"` // "global" or "section"
	TargetSectionID *string `json:"target_section_id"`
	Comment         string  `json:"comment" binding:"required"`
	CreatedBy       string  `json:"created_by"`
}

// AddFeedback adds feedback to an outline or draft
// POST /api/blog/documents/:id/outlines/:versionId/feedback
// POST /api/blog/documents/:id/drafts/:versionId/feedback
func (h *BlogDocumentsHandler) AddFeedback(c *gin.Context) {
	documentID := c.Param("id")

	var req AddFeedbackRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	targetType := models.FeedbackTargetType(req.TargetType)
	if targetType != models.FeedbackTargetOutline && targetType != models.FeedbackTargetDraft {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid target_type. Must be 'outline' or 'draft'",
		})
		return
	}

	scope := models.FeedbackScope(req.Scope)
	if scope != models.FeedbackScopeGlobal && scope != models.FeedbackScopeSection {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid scope. Must be 'global' or 'section'",
		})
		return
	}

	feedback, err := h.docRepo.AddFeedback(documentID, targetType, req.TargetVersionID, scope, req.TargetSectionID, req.Comment, req.CreatedBy)
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error adding feedback: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    feedback,
	})
}

// GenerateDraftRequest is the request body for generating a draft
type GenerateDraftRequest struct {
	Tone   string `json:"tone"`
	Length string `json:"length"`
	UseRAG bool   `json:"use_rag"`
}

// GenerateDraft generates a draft from an approved outline
// POST /api/blog/documents/:id/drafts
func (h *BlogDocumentsHandler) GenerateDraft(c *gin.Context) {
	documentID := c.Param("id")

	// Verify document exists
	doc, err := h.docRepo.FindByID(documentID)
	if err != nil || doc == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Document not found",
		})
		return
	}

	// Get approved outline
	approvedOutline, err := h.docRepo.GetApprovedOutlineVersion(documentID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if approvedOutline == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "No approved outline found. Please approve an outline first.",
		})
		return
	}

	var req GenerateDraftRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		// Use defaults
		req.Tone = "professional"
		req.Length = "medium"
		req.UseRAG = false
	}

	// Find blog agent
	agent, err := h.agentRepo.FindByType("blog")
	if err != nil || agent == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Blog agent not found",
		})
		return
	}

	// Get next version number
	nextVersion, err := h.docRepo.GetNextDraftVersion(documentID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Get feedback for the approved outline
	feedback, _ := h.docRepo.GetFeedbackForVersion(approvedOutline.ID)

	// Create task for draft generation
	input := map[string]any{
		"document_id":        documentID,
		"outline_version_id": approvedOutline.ID,
		"brand":              string(doc.Brand),
		"topic":              doc.Topic,
		"target_audience":    doc.TargetAudience,
		"intent":             doc.Intent,
		"outline_structure":  json.RawMessage(approvedOutline.Structure),
		"tone":               req.Tone,
		"length":             req.Length,
		"version":            nextVersion,
		"use_rag":            req.UseRAG,
		"feedback":           feedback,
	}

	task, err := h.taskRepo.Create(agent.ID, "generate_draft_v2", input, "medium", "")
	if err != nil {
		log.Printf("[BlogDocumentsHandler] Error creating task: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Execute task asynchronously
	go func() {
		h.taskRepo.UpdateStatus(task.ID, models.TaskStatusProcessing)

		// Draft generation can take longer on local models + RAG.
		ctx, cancel := context.WithTimeout(context.Background(), 25*60*1000000000) // 25 minutes
		defer cancel()

		tool, exists := tools.GetToolByAgentType(agent.Type)
		if !exists {
			h.taskRepo.UpdateFailed(task.ID, "No CLI tool configured for blog agent")
			return
		}

		cliInput := map[string]any{
			"action":  "generate_draft_v2",
			"task_id": task.ID,
		}
		for k, v := range input {
			cliInput[k] = v
		}

		result, err := h.executor.Execute(ctx, tool, cliInput)
		if err != nil {
			log.Printf("[BlogDocumentsHandler] Task execution error: %v", err)
			h.taskRepo.UpdateFailed(task.ID, err.Error())
			return
		}

		if result.Status == "failed" {
			h.taskRepo.UpdateFailed(task.ID, result.Error)
		} else {
			h.taskRepo.UpdateCompleted(task.ID, result.Output)

			// Save draft to DB from Go (Python subprocess may not have DB access).
			if err := h.saveDraftFromResult(result.Output, documentID, &approvedOutline.ID, nextVersion); err != nil {
				log.Printf("[BlogDocumentsHandler] Failed to save draft to DB: %v", err)
			}
		}
	}()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    task,
		"message": "Draft generation started",
	})
}

// saveDraftFromResult parses the executor output and saves the draft to the DB.
func (h *BlogDocumentsHandler) saveDraftFromResult(output map[string]any, documentID string, outlineVersionID *string, version int) error {
	if output == nil {
		return fmt.Errorf("output is nil")
	}

	response, ok := output["response"].(map[string]any)
	if !ok {
		return fmt.Errorf("output.response is missing or not an object")
	}

	content, _ := response["content"].(string)
	metaDescription, _ := response["meta_description"].(string)

	var wordCount, readingTime *int
	if wc, ok := response["word_count"].(float64); ok {
		val := int(wc)
		wordCount = &val
	}
	if rt, ok := response["estimated_reading_time"].(float64); ok {
		val := int(rt)
		readingTime = &val
	}

	_, err := h.docRepo.CreateDraftVersion(documentID, outlineVersionID, version, content, metaDescription, wordCount, readingTime, models.BlogVersionStatusDraft)
	if err != nil {
		return fmt.Errorf("failed to create draft version: %w", err)
	}

	log.Printf("[BlogDocumentsHandler] Saved draft version %d for document %s", version, documentID)
	return nil
}
