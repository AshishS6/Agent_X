package handlers

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"go-backend/internal/integrations"
	"go-backend/internal/models"
	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

type WorkflowsHandler struct {
	workflowRepo *models.WorkflowRepository
	runRepo      *models.WorkflowRunRepository
	stepRepo     *models.WorkflowStepRunRepository
	caseRepo     *models.WorkflowCaseRepository
	agentRepo    *models.AgentRepository
	taskRepo     *models.TaskRepository
	executor     *tools.Executor
}

func NewWorkflowsHandler(executor *tools.Executor) *WorkflowsHandler {
	return &WorkflowsHandler{
		workflowRepo: models.NewWorkflowRepository(),
		runRepo:      models.NewWorkflowRunRepository(),
		stepRepo:     models.NewWorkflowStepRunRepository(),
		caseRepo:     models.NewWorkflowCaseRepository(),
		agentRepo:    models.NewAgentRepository(),
		taskRepo:     models.NewTaskRepository(),
		executor:     executor,
	}
}

// ---- Workflow CRUD ----

type CreateWorkflowRequest struct {
	Name          string         `json:"name" binding:"required"`
	Description   string         `json:"description"`
	Status        string         `json:"status"`
	TriggerType   string         `json:"trigger_type" binding:"required"`
	TriggerConfig map[string]any `json:"trigger_config"`
	Steps         any            `json:"steps" binding:"required"`
	OwnerTeam     string         `json:"owner_team"`
	CreatedBy     string         `json:"created_by"`
}

// GetAll lists workflows
// GET /api/workflows
func (h *WorkflowsHandler) GetAll(c *gin.Context) {
	items, err := h.workflowRepo.FindAll()
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching workflows: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": items})
}

// Create creates workflow
// POST /api/workflows
func (h *WorkflowsHandler) Create(c *gin.Context) {
	var req CreateWorkflowRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": err.Error()})
		return
	}

	status := models.WorkflowStatusDraft
	if req.Status != "" {
		status = models.WorkflowStatus(req.Status)
	}
	if req.TriggerConfig == nil {
		req.TriggerConfig = map[string]any{}
	}

	wf, err := h.workflowRepo.Create(
		req.Name,
		req.Description,
		status,
		req.TriggerType,
		req.TriggerConfig,
		req.Steps,
		req.OwnerTeam,
		req.CreatedBy,
	)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error creating workflow: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": wf})
}

// GetByID returns workflow by id
// GET /api/workflows/:id
func (h *WorkflowsHandler) GetByID(c *gin.Context) {
	id := c.Param("id")
	wf, err := h.workflowRepo.FindByID(id)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching workflow %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if wf == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": wf})
}

// Update updates workflow
// PUT /api/workflows/:id
func (h *WorkflowsHandler) Update(c *gin.Context) {
	id := c.Param("id")
	var updates map[string]any
	if err := c.ShouldBindJSON(&updates); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": err.Error()})
		return
	}
	wf, err := h.workflowRepo.Update(id, updates)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error updating workflow %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if wf == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": wf})
}

// Pause explicitly pauses workflow
// POST /api/workflows/:id/pause
func (h *WorkflowsHandler) Pause(c *gin.Context) {
	id := c.Param("id")
	wf, err := h.workflowRepo.Update(id, map[string]any{"status": string(models.WorkflowStatusPaused)})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if wf == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": wf})
}

// Activate explicitly activates workflow
// POST /api/workflows/:id/activate
func (h *WorkflowsHandler) Activate(c *gin.Context) {
	id := c.Param("id")
	wf, err := h.workflowRepo.Update(id, map[string]any{"status": string(models.WorkflowStatusActive)})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if wf == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": wf})
}

// ---- Runs APIs ----

// GetRuns lists runs for a workflow
// GET /api/workflows/:id/runs?limit=&offset=
func (h *WorkflowsHandler) GetRuns(c *gin.Context) {
	workflowID := c.Param("id")

	limit := 20
	offset := 0
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 {
			limit = v
		}
	}
	if o := c.Query("offset"); o != "" {
		if v, err := strconv.Atoi(o); err == nil && v >= 0 {
			offset = v
		}
	}

	runs, total, err := h.runRepo.FindByWorkflowID(workflowID, limit, offset)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching runs for workflow %s: %v", workflowID, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": runs, "total": total})
}

// GetAllRuns lists all workflow runs
// GET /api/workflow-runs?limit=&offset=
func (h *WorkflowsHandler) GetAllRuns(c *gin.Context) {
	limit := 20
	offset := 0
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 {
			limit = v
		}
	}
	if o := c.Query("offset"); o != "" {
		if v, err := strconv.Atoi(o); err == nil && v >= 0 {
			offset = v
		}
	}

	runs, total, err := h.runRepo.FindAll(limit, offset)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching all runs: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": runs, "total": total})
}

// GetRunByID returns a run + its step runs
// GET /api/workflow-runs/:runId
func (h *WorkflowsHandler) GetRunByID(c *gin.Context) {
	runID := c.Param("runId")

	run, err := h.runRepo.FindByID(runID)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching run %s: %v", runID, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if run == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow run not found"})
		return
	}

	steps, err := h.stepRepo.FindByRunID(runID)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching step runs for run %s: %v", runID, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"run":   run,
			"steps": steps,
		},
	})
}

// ---- Cases APIs ----

// GetCases lists cases for a workflow
// GET /api/workflows/:id/cases?limit=&offset=
func (h *WorkflowsHandler) GetCases(c *gin.Context) {
	workflowID := c.Param("id")

	limit := 20
	offset := 0
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 {
			limit = v
		}
	}
	if o := c.Query("offset"); o != "" {
		if v, err := strconv.Atoi(o); err == nil && v >= 0 {
			offset = v
		}
	}

	cases, total, err := h.caseRepo.ListByWorkflowID(workflowID, limit, offset)
	if err != nil {
		log.Printf("[WorkflowsHandler] Error fetching cases for workflow %s: %v", workflowID, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": cases, "total": total})
}

// GetCaseByID returns a case by ID
// GET /api/workflow-cases/:caseId
func (h *WorkflowsHandler) GetCaseByID(c *gin.Context) {
	caseID := c.Param("caseId")
	caseRow, err := h.caseRepo.FindByID(caseID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if caseRow == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow case not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"success": true, "data": caseRow})
}

// GetRunsForCase returns runs for a case
// GET /api/workflow-cases/:caseId/runs?limit=&offset=
func (h *WorkflowsHandler) GetRunsForCase(c *gin.Context) {
	caseID := c.Param("caseId")

	limit := 20
	offset := 0
	if l := c.Query("limit"); l != "" {
		if v, err := strconv.Atoi(l); err == nil && v > 0 {
			limit = v
		}
	}
	if o := c.Query("offset"); o != "" {
		if v, err := strconv.Atoi(o); err == nil && v >= 0 {
			offset = v
		}
	}

	runs, total, err := h.runRepo.FindByCaseID(caseID, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": runs, "total": total})
}

// ---- Freshdesk trigger endpoint ----

// TriggerFreshdesk receives a webhook-like payload and kicks off a workflow run.
// POST /api/triggers/freshdesk/:workflowId
func (h *WorkflowsHandler) TriggerFreshdesk(c *gin.Context) {
	workflowID := c.Param("workflowId")

	// Resolve workflow (and ensure it is active)
	wf, err := h.workflowRepo.FindByID(workflowID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if wf == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Workflow not found"})
		return
	}
	if wf.Status != models.WorkflowStatusActive {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Workflow is not active"})
		return
	}
	if wf.TriggerType != "freshdesk" {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Workflow trigger_type is not freshdesk"})
		return
	}

	// Parse trigger_config
	triggerCfg := map[string]any{}
	_ = json.Unmarshal(wf.TriggerConfig, &triggerCfg)
	secretHeader := "X-AgentX-Webhook-Secret"
	if hdr, ok := triggerCfg["header"].(string); ok && hdr != "" {
		secretHeader = hdr
	}
	expectedSecret, _ := triggerCfg["secret"].(string)
	if expectedSecret == "" {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Workflow trigger_config.secret is not set"})
		return
	}
	if got := c.GetHeader(secretHeader); got == "" || got != expectedSecret {
		c.JSON(http.StatusUnauthorized, gin.H{"success": false, "error": "Invalid webhook secret"})
		return
	}

	// Read raw body once and parse JSON
	bodyBytes, err := io.ReadAll(c.Request.Body)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Failed to read request body"})
		return
	}
	// Restore body for any downstream middleware (defensive)
	c.Request.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

	var payload map[string]any
	if len(bytes.TrimSpace(bodyBytes)) == 0 {
		payload = map[string]any{}
	} else if err := json.Unmarshal(bodyBytes, &payload); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Invalid JSON payload"})
		return
	}

	// Determine idempotency key (header first; else based on known fields; else hash of body)
	var idempotencyKey *string
	if hdr := c.GetHeader("X-Idempotency-Key"); hdr != "" {
		idempotencyKey = &hdr
	}

	// Ticket id (case correlation)
	ticketID := getString(payload, "ticket_id", "ticketId")
	if ticketID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": "Missing ticket_id in payload"})
		return
	}

	// Provider event id (preferred idempotency)
	providerEventID := getString(payload, "provider_event_id", "event_id", "conversation_id", "providerEventId", "eventId", "conversationId")
	if providerEventID != "" {
		// Normalize to avoid collisions across tickets
		normalized := "freshdesk:" + ticketID + ":" + providerEventID
		providerEventID = normalized
	}

	// Fallback idempotency if provider event id missing
	if idempotencyKey == nil {
		eventType := getString(payload, "event_type", "eventType")
		updatedAt := getString(payload, "updated_at", "updatedAt")
		if ticketID != "" && eventType != "" && updatedAt != "" {
			key := ticketID + ":" + eventType + ":" + updatedAt
			sum := sha256.Sum256([]byte(key))
			hash := hex.EncodeToString(sum[:])
			idempotencyKey = &hash
		} else if ticketID != "" && eventType != "" {
			// MVP fallback: hash a stable subset (avoid full body which can include signatures/noise)
			subject := getString(payload, "subject")
			description := getString(payload, "description", "body", "body_text")
			requester := getString(payload, "requester_email", "requesterEmail", "email")
			priority := getString(payload, "priority")
			key := ticketID + ":" + eventType + ":" + subject + ":" + description + ":" + requester + ":" + priority
			sum := sha256.Sum256([]byte(key))
			hash := hex.EncodeToString(sum[:])
			idempotencyKey = &hash
		} else if len(bodyBytes) > 0 {
			sum := sha256.Sum256(bodyBytes)
			hash := hex.EncodeToString(sum[:])
			idempotencyKey = &hash
		}
	}

	// Idempotency short-circuit
	if providerEventID != "" {
		existing, err := h.runRepo.FindByProviderEventID(workflowID, providerEventID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
			return
		}
		if existing != nil {
			c.JSON(http.StatusOK, gin.H{"success": true, "data": existing, "message": "Duplicate trigger ignored (provider_event_id idempotent)"})
			return
		}
	}
	if idempotencyKey != nil {
		existing, err := h.runRepo.FindByIdempotencyKey(workflowID, *idempotencyKey)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
			return
		}
		if existing != nil {
			c.JSON(http.StatusOK, gin.H{"success": true, "data": existing, "message": "Duplicate trigger ignored (idempotent)"})
			return
		}
	}

	// Resolve or create case for this ticket
	caseRow, err := h.caseRepo.FindOrCreateByExternalRef(workflowID, "freshdesk", ticketID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	// Create run
	var providerEventIDPtr *string
	if providerEventID != "" {
		providerEventIDPtr = &providerEventID
	}
	run, err := h.runRepo.Create(workflowID, &caseRow.ID, providerEventIDPtr, idempotencyKey, payload)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	// Execute workflow asynchronously (sequential steps)
	go h.executeWorkflowRun(run, wf)

	c.JSON(http.StatusOK, gin.H{"success": true, "data": run})
}

func (h *WorkflowsHandler) executeWorkflowRun(run *models.WorkflowRun, wf *models.Workflow) {
	// Parse step definitions
	var steps []map[string]any
	if err := json.Unmarshal(wf.Steps, &steps); err != nil {
		log.Printf("[Workflows] ❌ run=%s workflow=%s invalid steps JSON", run.ID, wf.ID)
		_ = h.runRepo.MarkFailed(run.ID, "Invalid workflow steps JSON")
		return
	}

	log.Printf("[Workflows] ▶️ run=%s workflow=%s steps=%d", run.ID, wf.ID, len(steps))

	var lastOutput any = nil

	for idx, stepDef := range steps {
		stepType, _ := stepDef["type"].(string)
		if stepType == "" {
			stepType = "unknown"
		}

		// Compute step input
		input := map[string]any{
			"trigger":  json.RawMessage(run.TriggerPayload),
			"previous": lastOutput,
			"step":     stepDef,
		}

		// Special-case "load_context" step type (Freshdesk)
		if stepType == "load_context" {
			out, errMsg := h.executeLoadContextStep(run, idx, stepDef)
			lastOutput = out
			if errMsg != "" {
				log.Printf("[Workflows] ❌ run=%s step=%d type=load_context error=%s", run.ID, idx, errMsg)
				_ = h.runRepo.MarkFailed(run.ID, errMsg)
				return
			}
			continue
		}

		// Special-case "agent_task" step type
		if stepType == "agent_task" {
			out, errMsg := h.executeAgentTaskStep(run, idx, stepDef, lastOutput)
			lastOutput = out
			if errMsg != "" {
				log.Printf("[Workflows] ❌ run=%s step=%d type=agent_task error=%s", run.ID, idx, errMsg)
				_ = h.runRepo.MarkFailed(run.ID, errMsg)
				return
			}
			continue
		}

		// Default: record step as skipped with debug output
		stepRun, err := h.stepRepo.Create(run.ID, idx, stepType, input)
		if err != nil {
			_ = h.runRepo.MarkFailed(run.ID, "Failed to create step run")
			return
		}
		_ = h.stepRepo.UpdateCompleted(stepRun.ID, map[string]any{
			"status":  "skipped",
			"message": "Step type not implemented in MVP",
		}, nil)
		lastOutput = map[string]any{"skipped": true, "type": stepType}
	}

	_ = h.runRepo.MarkCompleted(run.ID)
	log.Printf("[Workflows] ✅ run=%s workflow=%s completed", run.ID, wf.ID)
}

func (h *WorkflowsHandler) executeLoadContextStep(run *models.WorkflowRun, stepIndex int, stepDef map[string]any) (any, string) {
	// Determine ticket_id from trigger payload or step input
	trigger := map[string]any{}
	_ = json.Unmarshal(run.TriggerPayload, &trigger)

	ticketID := getString(trigger, "ticket_id", "ticketId")
	if rawInput, ok := stepDef["input"].(map[string]any); ok {
		if v, ok := rawInput["ticket_id"].(string); ok && v != "" {
			ticketID = v
		}
	}
	if tmpl, ok := stepDef["input_template"].(map[string]any); ok {
		if v, ok := tmpl["ticket_id"]; ok {
			if s, ok := resolveTemplateValue(v, trigger).(string); ok && s != "" {
				ticketID = s
			}
		}
	}
	if ticketID == "" {
		stepRun, _ := h.stepRepo.Create(run.ID, stepIndex, "load_context", map[string]any{"error": "Missing ticket_id"})
		if stepRun != nil {
			_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{"error": "Missing ticket_id"}, "Missing ticket_id", nil)
		}
		return map[string]any{"error": "Missing ticket_id"}, "Missing ticket_id"
	}

	stepRun, err := h.stepRepo.Create(run.ID, stepIndex, "load_context", map[string]any{
		"ticket_id": ticketID,
	})
	if err != nil {
		return map[string]any{"error": "Failed to create step run"}, "Failed to create step run"
	}

	client, err := integrations.NewFreshdeskClientFromEnv()
	if err != nil {
		out := map[string]any{"ticket_id": ticketID, "error": err.Error()}
		_ = h.stepRepo.UpdateFailed(stepRun.ID, out, err.Error(), nil)
		return out, err.Error()
	}

	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()

	ticket, err := client.GetTicket(ctx, ticketID)
	if err != nil {
		out := map[string]any{"ticket_id": ticketID, "error": err.Error()}
		_ = h.stepRepo.UpdateFailed(stepRun.ID, out, err.Error(), nil)
		return out, err.Error()
	}
	conversations, err := client.ListConversations(ctx, ticketID)
	if err != nil {
		out := map[string]any{"ticket_id": ticketID, "ticket": ticket, "error": err.Error()}
		_ = h.stepRepo.UpdateFailed(stepRun.ID, out, err.Error(), nil)
		return out, err.Error()
	}

	// Load previous case state (to produce deltas and reduce noise)
	var prevLastSeen string
	var prevTicketSnapshot map[string]any
	if run.CaseID != nil && *run.CaseID != "" {
		caseRow, err := h.caseRepo.FindByID(*run.CaseID)
		if err == nil && caseRow != nil && len(caseRow.LatestState) > 0 {
			var prevState map[string]any
			if err := json.Unmarshal(caseRow.LatestState, &prevState); err == nil && prevState != nil {
				prevLastSeen = getString(prevState, "last_seen_conversation_id")
				if ts, ok := prevState["ticket_snapshot"].(map[string]any); ok {
					prevTicketSnapshot = ts
				}
			}
		}
	}

	compactTicket := compactFreshdeskTicket(ticket)
	compactConversations := compactFreshdeskConversations(conversations, 20)

	lastConvID := ""
	if len(compactConversations) > 0 {
		lastConvID = getString(compactConversations[len(compactConversations)-1], "id")
	}

	// Conversation delta for LLM: only new messages since last_seen (plus a small continuity window)
	llmConversations := buildConversationDeltaForLLM(compactConversations, prevLastSeen, 8, 3)

	latestRequester := ""
	lastAgent := ""
	for i := len(compactConversations) - 1; i >= 0; i-- {
		conv := compactConversations[i]
		body := getString(conv, "body_text")
		incoming := false
		if v, ok := conv["incoming"]; ok {
			if b, ok := v.(bool); ok {
				incoming = b
			}
		}
		if latestRequester == "" && incoming && body != "" {
			latestRequester = body
		}
		if lastAgent == "" && !incoming && body != "" {
			lastAgent = body
		}
		if latestRequester != "" && lastAgent != "" {
			break
		}
	}

	// Ticket delta for LLM: include only changed fields (but always keep minimal identity fields)
	llmTicket := compactTicket
	ticketChanges := map[string]any{}
	if prevTicketSnapshot != nil {
		ticketChanges = diffMap(prevTicketSnapshot, compactTicket)
		llmTicket = ensureTicketIdentityFields(ticketChanges, compactTicket)
	}

	llmContext := map[string]any{
		"ticket_id":                 ticketID,
		"ticket":                    llmTicket,
		"ticket_changes":            ticketChanges,
		"conversations":             llmConversations,
		"latest_requester_message":  latestRequester,
		"last_agent_message":        lastAgent,
		"last_seen_conversation_id": lastConvID,
	}
	llmContext = pruneEmpty(llmContext).(map[string]any)

	out := map[string]any{
		"ticket_id":                 ticketID,
		"ticket":                    compactTicket,
		"conversations":             compactConversations,
		"latest_requester_message":  latestRequester,
		"last_agent_message":        lastAgent,
		"last_seen_conversation_id": lastConvID,
		"llm_context":               llmContext,
	}

	_ = h.stepRepo.UpdateCompleted(stepRun.ID, out, nil)

	// Update case latest_state if present
	if run.CaseID != nil && *run.CaseID != "" {
		_ = h.caseRepo.UpdateLatestState(*run.CaseID, map[string]any{
			"ticket_id":                 ticketID,
			"last_seen_conversation_id": lastConvID,
			"ticket_snapshot":           compactTicket,
			"updated_at":                time.Now().UTC().Format(time.RFC3339),
		})
	}

	return out, ""
}

func (h *WorkflowsHandler) executeAgentTaskStep(run *models.WorkflowRun, stepIndex int, stepDef map[string]any, previous any) (any, string) {
	agentType, _ := stepDef["agent_type"].(string)
	action, _ := stepDef["action"].(string)
	if agentType == "" || action == "" {
		// Still persist step output for debugging
		stepRun, _ := h.stepRepo.Create(run.ID, stepIndex, "agent_task", stepDef)
		if stepRun != nil {
			_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{
				"error": "Missing agent_type or action",
				"step":  stepDef,
			}, "Missing agent_type or action", nil)
		}
		return map[string]any{"error": "Missing agent_type or action"}, "Invalid step definition"
	}

	// Input mapping: input_template supports {{key}} substitution from trigger payload
	trigger := map[string]any{}
	_ = json.Unmarshal(run.TriggerPayload, &trigger)
	input := map[string]any{}
	if tmpl, ok := stepDef["input_template"].(map[string]any); ok {
		for k, v := range tmpl {
			input[k] = resolveTemplateValue(v, trigger)
		}
	} else if rawInput, ok := stepDef["input"].(map[string]any); ok {
		input = rawInput
	}

	// Always include previous step output for context (especially load_context)
	if previous != nil {
		// If previous step provided an llm_context, pass that to avoid noise
		if prevMap, ok := previous.(map[string]any); ok {
			if lc, ok := prevMap["llm_context"]; ok && lc != nil {
				input["context"] = lc
			} else {
				input["context"] = previous
			}
		} else {
			input["context"] = previous
		}
	}

	stepRun, err := h.stepRepo.Create(run.ID, stepIndex, "agent_task", map[string]any{
		"agent_type": agentType,
		"action":     action,
		"input":      input,
	})
	if err != nil {
		return map[string]any{"error": "Failed to create step run"}, "Failed to create step run"
	}

	agent, err := h.agentRepo.FindByType(agentType)
	if err != nil {
		_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{"error": err.Error()}, err.Error(), nil)
		return map[string]any{"error": err.Error()}, err.Error()
	}
	if agent == nil {
		// Auto-seed missing agent row from tool registry (common on existing DBs)
		if toolByName, ok := tools.GetTool(agentType); ok {
			_ = h.agentRepo.EnsureByType(agentType, toolByName.Name, toolByName.Description, models.AgentStatusActive)
		} else if toolByType, ok := tools.GetToolByAgentType(agentType); ok {
			_ = h.agentRepo.EnsureByType(agentType, toolByType.Name, toolByType.Description, models.AgentStatusActive)
		}

		agent, err = h.agentRepo.FindByType(agentType)
		if err != nil {
			_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{"error": err.Error()}, err.Error(), nil)
			return map[string]any{"error": err.Error()}, err.Error()
		}
		if agent == nil {
			msg := "Agent not found: " + agentType
			_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{"error": msg}, msg, nil)
			return map[string]any{"error": msg}, msg
		}
	}
	if agent.Status != models.AgentStatusActive {
		msg := "Agent is not active: " + agentType
		_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{"error": msg}, msg, nil)
		return map[string]any{"error": msg}, msg
	}

	tool, exists := tools.GetToolByAgentType(agent.Type)
	if !exists {
		msg := "No CLI tool configured for agent type: " + agent.Type
		_ = h.stepRepo.UpdateFailed(stepRun.ID, map[string]any{"error": msg}, msg, nil)
		return map[string]any{"error": msg}, msg
	}

	priority := "medium"
	if p, ok := input["priority"].(string); ok && p != "" {
		priority = p
	}

	// Always write step output (even on failure). Retry once on execution failure.
	stepOutput := map[string]any{
		"agent_type":   agentType,
		"action":       action,
		"tool_timeout": tool.Timeout.String(),
		"cli_input":    input,
		"attempts":     []map[string]any{},
	}

	var lastTaskID *string
	var lastErr string

	for attempt := 1; attempt <= 2; attempt++ {
		task, err := h.taskRepo.Create(agent.ID, action, input, priority, "")
		if err != nil {
			lastErr = err.Error()
			stepOutput["attempts"] = append(stepOutput["attempts"].([]map[string]any), map[string]any{
				"attempt": attempt,
				"status":  "failed",
				"error":   lastErr,
			})
			break
		}
		lastTaskID = &task.ID

		_ = h.taskRepo.UpdateStatus(task.ID, models.TaskStatusProcessing)
		ctx, cancel := context.WithTimeout(context.Background(), tool.Timeout)

		cliInput := map[string]any{
			"action":  action,
			"task_id": task.ID,
		}
		for k, v := range input {
			cliInput[k] = v
		}

		start := time.Now()
		result, execErr := h.executor.Execute(ctx, tool, cliInput)
		durationMs := time.Since(start).Milliseconds()
		cancel()

		attemptOutput := map[string]any{
			"attempt":     attempt,
			"task_id":     task.ID,
			"duration_ms": durationMs,
		}

		if execErr != nil {
			lastErr = execErr.Error()
			_ = h.taskRepo.UpdateFailed(task.ID, lastErr)
			attemptOutput["status"] = "failed"
			attemptOutput["error"] = lastErr
			stepOutput["attempts"] = append(stepOutput["attempts"].([]map[string]any), attemptOutput)

			if attempt == 1 {
				time.Sleep(750 * time.Millisecond)
				continue
			}
			break
		}

		if result.Status == "failed" {
			lastErr = result.Error
			_ = h.taskRepo.UpdateFailed(task.ID, lastErr)
			attemptOutput["status"] = "failed"
			attemptOutput["error"] = lastErr
			attemptOutput["result"] = result.Output
			stepOutput["attempts"] = append(stepOutput["attempts"].([]map[string]any), attemptOutput)

			if attempt == 1 {
				time.Sleep(750 * time.Millisecond)
				continue
			}
			break
		}

		_ = h.taskRepo.UpdateCompleted(task.ID, result.Output)
		attemptOutput["status"] = "completed"
		attemptOutput["result"] = result.Output
		stepOutput["attempts"] = append(stepOutput["attempts"].([]map[string]any), attemptOutput)
		stepOutput["status"] = "completed"
		stepOutput["task_id"] = task.ID
		stepOutput["result"] = result.Output

		_ = h.stepRepo.UpdateCompleted(stepRun.ID, stepOutput, &task.ID)
		return stepOutput, ""
	}

	stepOutput["status"] = "failed"
	stepOutput["error"] = lastErr
	_ = h.stepRepo.UpdateFailed(stepRun.ID, stepOutput, lastErr, lastTaskID)
	return stepOutput, lastErr
}

func resolveTemplateValue(v any, trigger map[string]any) any {
	// Minimal templating: strings like "{{field}}" map to trigger[field]
	s, ok := v.(string)
	if !ok {
		return v
	}
	if len(s) >= 4 && s[0:2] == "{{" && s[len(s)-2:] == "}}" {
		key := s[2 : len(s)-2]
		if val, ok := trigger[key]; ok {
			return val
		}
	}
	return v
}

func getString(m map[string]any, keys ...string) string {
	for _, k := range keys {
		if v, ok := m[k]; ok {
			if s, ok := v.(string); ok && s != "" {
				return s
			}
			// allow numeric ids
			if f, ok := v.(float64); ok && f != 0 {
				return strconv.FormatInt(int64(f), 10)
			}
		}
	}
	return ""
}

// ---- Freshdesk payload compaction / pruning helpers ----

func compactFreshdeskTicket(ticket map[string]any) map[string]any {
	if ticket == nil {
		return map[string]any{}
	}

	// Allowlist only: keep what’s useful for triage and routing.
	out := map[string]any{
		"id":         ticket["id"],
		"subject":    ticket["subject"],
		"status":     ticket["status"],
		"priority":   ticket["priority"],
		"tags":       ticket["tags"],
		"type":       ticket["type"],
		"group_id":   ticket["group_id"],
		"requester":  ticket["requester_id"],
		"responder":  ticket["responder_id"],
		"created_at": ticket["created_at"],
		"updated_at": ticket["updated_at"],
		"due_by":     ticket["due_by"],
		"fr_due_by":  ticket["fr_due_by"],
	}

	// Prefer plaintext description to avoid HTML noise.
	if dt, ok := ticket["description_text"]; ok {
		out["description_text"] = truncateString(asString(dt), 2000)
	}

	// Selected custom fields only (reduce noise).
	if cf, ok := ticket["custom_fields"].(map[string]any); ok && cf != nil {
		allow := []string{
			"cf_module",
			"cf_peg_product",
			"cf_peg_query_type",
			"cf_finance_related_sub_category",
			"cf_finance_related_subcategory",
			"cf_finance_related_sub_category_1",
		}
		custom := map[string]any{}
		for _, k := range allow {
			if v, ok := cf[k]; ok {
				custom[k] = v
			}
		}
		out["custom_fields"] = custom
	}

	// Attachments: keep metadata only, drop signed URLs.
	if atts, ok := ticket["attachments"].([]any); ok && len(atts) > 0 {
		comp := []map[string]any{}
		for _, a := range atts {
			m, ok := a.(map[string]any)
			if !ok || m == nil {
				continue
			}
			comp = append(comp, map[string]any{
				"id":           m["id"],
				"name":         m["name"],
				"size":         m["size"],
				"content_type": m["content_type"],
			})
		}
		out["attachments"] = comp
	}

	pruned := pruneEmpty(out)
	if m, ok := pruned.(map[string]any); ok {
		return m
	}
	return map[string]any{}
}

func compactFreshdeskConversations(convs []map[string]any, maxItems int) []map[string]any {
	if len(convs) == 0 {
		return []map[string]any{}
	}

	// Keep only the most recent maxItems (Freshdesk usually returns oldest->newest).
	start := 0
	if maxItems > 0 && len(convs) > maxItems {
		start = len(convs) - maxItems
	}

	out := []map[string]any{}
	for i := start; i < len(convs); i++ {
		conv := convs[i]
		body := conv["body_text"]
		if asString(body) == "" {
			// fallback: avoid HTML if possible, but keep small snippet if body_text missing
			body = truncateString(cleanWhitespace(asString(conv["body"])), 1200)
		} else {
			body = truncateString(cleanWhitespace(asString(body)), 2000)
		}

		item := map[string]any{
			"id":         conv["id"],
			"created_at": conv["created_at"],
			"incoming":   conv["incoming"],
			"private":    conv["private"],
			"source":     conv["source"],
			"from_email": conv["from_email"],
			"to_emails":  conv["to_emails"],
			"cc_emails":  conv["cc_emails"],
			"body_text":  body,
		}

		pruned := pruneEmpty(item)
		if m, ok := pruned.(map[string]any); ok {
			out = append(out, m)
		}
	}
	return out
}

func buildConversationDeltaForLLM(convs []map[string]any, prevLastSeen string, maxItems int, continuity int) []map[string]any {
	if len(convs) == 0 {
		return []map[string]any{}
	}
	if prevLastSeen == "" {
		return tailConversations(convs, maxItems)
	}

	// Find the index of prevLastSeen; take items after it plus a small continuity window.
	idx := -1
	for i := 0; i < len(convs); i++ {
		if getString(convs[i], "id") == prevLastSeen {
			idx = i
			break
		}
	}
	if idx == -1 {
		return tailConversations(convs, maxItems)
	}

	start := idx + 1
	if continuity > 0 {
		contStart := idx - continuity + 1
		if contStart < 0 {
			contStart = 0
		}
		start = contStart
	}

	if start < 0 {
		start = 0
	}

	sub := convs[start:]
	return tailConversations(sub, maxItems)
}

func tailConversations(convs []map[string]any, maxItems int) []map[string]any {
	if maxItems <= 0 || len(convs) <= maxItems {
		return convs
	}
	return convs[len(convs)-maxItems:]
}

func ensureTicketIdentityFields(delta map[string]any, full map[string]any) map[string]any {
	if delta == nil {
		delta = map[string]any{}
	}
	// Always include identity fields so the LLM knows what it’s looking at.
	identity := []string{"id", "subject", "status", "priority"}
	for _, k := range identity {
		if _, ok := delta[k]; !ok {
			if v, ok2 := full[k]; ok2 {
				delta[k] = v
			}
		}
	}
	return delta
}

func diffMap(prev map[string]any, curr map[string]any) map[string]any {
	out := map[string]any{}
	if curr == nil {
		return out
	}
	for k, v := range curr {
		if prev == nil {
			out[k] = v
			continue
		}
		pv, ok := prev[k]
		if !ok {
			out[k] = v
			continue
		}
		if !jsonEqual(pv, v) {
			out[k] = v
		}
	}
	return out
}

func jsonEqual(a any, b any) bool {
	aj, err1 := json.Marshal(a)
	bj, err2 := json.Marshal(b)
	if err1 != nil || err2 != nil {
		return false
	}
	return string(aj) == string(bj)
}

func pruneEmpty(v any) any {
	switch t := v.(type) {
	case map[string]any:
		out := map[string]any{}
		for k, val := range t {
			p := pruneEmpty(val)
			if isEmptyValue(p) {
				continue
			}
			out[k] = p
		}
		if len(out) == 0 {
			return map[string]any{}
		}
		return out
	case []map[string]any:
		arr := []any{}
		for _, m := range t {
			arr = append(arr, m)
		}
		return pruneEmpty(arr)
	case []any:
		out := []any{}
		for _, val := range t {
			p := pruneEmpty(val)
			if isEmptyValue(p) {
				continue
			}
			out = append(out, p)
		}
		if len(out) == 0 {
			return []any{}
		}
		return out
	default:
		// Keep bool/number as-is; trim strings
		if s, ok := t.(string); ok {
			return strings.TrimSpace(s)
		}
		return v
	}
}

func isEmptyValue(v any) bool {
	if v == nil {
		return true
	}
	switch t := v.(type) {
	case string:
		return strings.TrimSpace(t) == ""
	case []any:
		return len(t) == 0
	case map[string]any:
		return len(t) == 0
	}
	return false
}

func truncateString(s string, max int) string {
	if max <= 0 {
		return s
	}
	if len(s) <= max {
		return s
	}
	return s[:max] + "…"
}

func asString(v any) string {
	if v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return ""
}

func cleanWhitespace(s string) string {
	// Minimal cleanup: collapse repeated spaces/newlines.
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	s = strings.TrimSpace(s)
	for strings.Contains(s, "\n\n\n") {
		s = strings.ReplaceAll(s, "\n\n\n", "\n\n")
	}
	for strings.Contains(s, "  ") {
		s = strings.ReplaceAll(s, "  ", " ")
	}
	return s
}
