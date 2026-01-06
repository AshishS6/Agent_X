package handlers

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"time"

	"go-backend/internal/models"
	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

// TasksHandler handles task-related HTTP requests
type TasksHandler struct {
	taskRepo *models.TaskRepository
	executor *tools.Executor
}

// NewTasksHandler creates a new tasks handler
func NewTasksHandler(executor *tools.Executor) *TasksHandler {
	return &TasksHandler{
		taskRepo: models.NewTaskRepository(),
		executor: executor,
	}
}

// GetAll returns all tasks with optional filters
// GET /api/tasks
func (h *TasksHandler) GetAll(c *gin.Context) {
	filters := make(map[string]any)

	if agentID := c.Query("agentId"); agentID != "" {
		filters["agentId"] = agentID
	}
	if status := c.Query("status"); status != "" {
		filters["status"] = status
	}
	if userID := c.Query("userId"); userID != "" {
		filters["userId"] = userID
	}
	if limitStr := c.Query("limit"); limitStr != "" {
		if limit, err := strconv.Atoi(limitStr); err == nil {
			filters["limit"] = limit
		}
	}
	if offsetStr := c.Query("offset"); offsetStr != "" {
		if offset, err := strconv.Atoi(offsetStr); err == nil {
			filters["offset"] = offset
		}
	}

	tasks, total, err := h.taskRepo.FindAll(filters)
	if err != nil {
		log.Printf("[TasksHandler] Error fetching tasks: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    tasks,
		"total":   total,
	})
}

// GetByID returns a task by ID
// GET /api/tasks/:id
func (h *TasksHandler) GetByID(c *gin.Context) {
	id := c.Param("id")

	task, err := h.taskRepo.FindByID(id)
	if err != nil {
		log.Printf("[TasksHandler] Error fetching task %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if task == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Task not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    task,
	})
}

// GetStatusCounts returns task counts by status
// GET /api/tasks/status/counts
func (h *TasksHandler) GetStatusCounts(c *gin.Context) {
	agentID := c.Query("agentId")

	counts, err := h.taskRepo.GetStatusCounts(agentID)
	if err != nil {
		log.Printf("[TasksHandler] Error fetching status counts: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    counts,
	})
}

// DownloadReport generates and downloads a report in the specified format
// GET /api/tasks/:id/report?format=pdf|json|markdown
func (h *TasksHandler) DownloadReport(c *gin.Context) {
	id := c.Param("id")
	format := c.Query("format")
	
	if format == "" {
		format = "json" // Default
	}
	
	if format != "pdf" && format != "json" && format != "markdown" {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid format. Must be pdf, json, or markdown",
		})
		return
	}
	
	// Get task
	task, err := h.taskRepo.FindByID(id)
	if err != nil {
		log.Printf("[TasksHandler] Error fetching task %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}
	
	if task == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Task not found",
		})
		return
	}
	
	// Validate task is completed
	if task.Status != models.TaskStatusCompleted {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Task must be completed to generate report",
		})
		return
	}
	
	// Extract scan data from task output
	var scanData map[string]any
	if task.Output != nil {
		if err := json.Unmarshal(task.Output, &scanData); err != nil {
			log.Printf("[TasksHandler] Error parsing task output: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"error":   "Failed to parse task output",
			})
			return
		}
	}
	
	// Get comprehensive_site_scan from response
	var finalScanData map[string]any
	if response, ok := scanData["response"].(string); ok {
		// response is a JSON string
		if err := json.Unmarshal([]byte(response), &finalScanData); err != nil {
			log.Printf("[TasksHandler] Error parsing response JSON: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"error":   "Failed to parse scan response",
			})
			return
		}
	} else if responseObj, ok := scanData["response"].(map[string]any); ok {
		// response is already an object
		finalScanData = responseObj
	} else {
		// Try direct access
		finalScanData = scanData
	}
	
	// Get market research tool
	tool, exists := tools.GetToolByAgentType("market_research")
	if !exists {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Market research tool not found",
		})
		return
	}
	
	// Prepare CLI input
	cliInput := map[string]any{
		"action":    "download_report",
		"task_id":   id,
		"format":     format,
		"scan_data": finalScanData,
	}
	
	// Execute report generation
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	
	result, err := h.executor.Execute(ctx, tool, cliInput)
	if err != nil {
		log.Printf("[TasksHandler] Report generation error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Report generation failed: " + err.Error(),
		})
		return
	}
	
	if result.Status == "failed" {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   result.Error,
		})
		return
	}
	
	// Extract content and content type
	output := result.Output
	contentType, ok := output["content_type"].(string)
	if !ok {
		contentType = "application/octet-stream"
	}
	content, ok := output["content"].(string)
	if !ok {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Invalid report content format",
		})
		return
	}
	
	// Decode base64 for PDF
	var fileContent []byte
	if format == "pdf" {
		fileContent, err = base64.StdEncoding.DecodeString(content)
		if err != nil {
			log.Printf("[TasksHandler] Error decoding PDF: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"success": false,
				"error":   "Failed to decode PDF content",
			})
			return
		}
	} else {
		fileContent = []byte(content)
	}
	
	// Generate filename
	url := ""
	if scan, ok := finalScanData["comprehensive_site_scan"].(map[string]any); ok {
		if urlStr, ok := scan["url"].(string); ok {
			url = urlStr
		}
	}
	domain := "site"
	if url != "" {
		// Extract domain from URL (simplified)
		domain = url
		if len(domain) > 50 {
			domain = domain[:50]
		}
		// Clean domain
		domain = sanitizeDomain(domain)
	}
	
	filename := generateFilename(domain, id, format)
	
	// Set headers - quote filename to handle special characters
	c.Header("Content-Type", contentType)
	c.Header("Content-Disposition", `attachment; filename="`+filename+`"`)
	c.Data(http.StatusOK, contentType, fileContent)
	
	// Log download event (audit logging)
	logDownloadEvent(id, format, task.UserID)
}

// Helper functions
func sanitizeDomain(domain string) string {
	// Remove protocol and path, keep only domain
	// Simple sanitization for filename
	result := ""
	for _, char := range domain {
		if (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || 
		   (char >= '0' && char <= '9') || char == '.' || char == '-' {
			result += string(char)
		} else {
			result += "_"
		}
	}
	if len(result) > 50 {
		result = result[:50]
	}
	return result
}

func generateFilename(domain string, scanID string, format string) string {
	date := time.Now().Format("2006-01-02")
	
	switch format {
	case "pdf":
		return "site_compliance_" + domain + "_" + scanID + "_" + date + ".pdf"
	case "json":
		return "site_scan_" + domain + "_" + scanID + ".json"
	case "markdown":
		return "site_report_" + domain + "_" + scanID + ".md"
	default:
		return "report_" + scanID + "." + format
	}
}

func logDownloadEvent(scanID string, format string, userID *string) {
	// TODO: Implement proper audit logging to database
	// For now, just log to console
	user := "unknown"
	if userID != nil {
		user = *userID
	}
	log.Printf("[Audit] Report download - scan_id: %s, format: %s, user_id: %s, timestamp: %s",
		scanID, format, user, time.Now().Format(time.RFC3339))
}
