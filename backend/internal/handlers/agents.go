package handlers

import (
	"context"
	"log"
	"net/http"

	"go-backend/internal/models"
	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

// AgentsHandler handles agent-related HTTP requests
type AgentsHandler struct {
	agentRepo *models.AgentRepository
	taskRepo  *models.TaskRepository
	executor  *tools.Executor
}

// NewAgentsHandler creates a new agents handler
func NewAgentsHandler(executor *tools.Executor) *AgentsHandler {
	return &AgentsHandler{
		agentRepo: models.NewAgentRepository(),
		taskRepo:  models.NewTaskRepository(),
		executor:  executor,
	}
}

// GetAll returns all agents
// GET /api/agents
func (h *AgentsHandler) GetAll(c *gin.Context) {
	agents, err := h.agentRepo.FindAll()
	if err != nil {
		log.Printf("[AgentsHandler] Error fetching agents: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    agents,
	})
}

// GetByID returns an agent by ID
// GET /api/agents/:id
func (h *AgentsHandler) GetByID(c *gin.Context) {
	id := c.Param("id")

	agent, err := h.agentRepo.FindByID(id)
	if err != nil {
		log.Printf("[AgentsHandler] Error fetching agent %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if agent == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Agent not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    agent,
	})
}

// ExecuteRequest is the request body for agent execution
type ExecuteRequest struct {
	Action   string         `json:"action" binding:"required"`
	Input    map[string]any `json:"input" binding:"required"`
	Priority string         `json:"priority"`
	UserID   string         `json:"userId"`
}

// Execute runs an agent with the given task
// POST /api/agents/:name/execute
// :name is the agent type (e.g., "market_research", "sales")
func (h *AgentsHandler) Execute(c *gin.Context) {
	name := c.Param("name")

	// Find agent by type (name)
	agent, err := h.agentRepo.FindByType(name)
	if err != nil {
		log.Printf("[AgentsHandler] Error fetching agent %s: %v", name, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if agent == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Agent not found: " + name,
		})
		return
	}

	// Check agent status
	if agent.Status != models.AgentStatusActive {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Agent is " + string(agent.Status) + ", cannot execute",
		})
		return
	}

	// Parse request body
	var req ExecuteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Missing required fields: action, input",
		})
		return
	}

	// Set default priority
	if req.Priority == "" {
		req.Priority = "medium"
	}

	// Find the corresponding tool by agent type
	tool, exists := tools.GetToolByAgentType(agent.Type)
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "No CLI tool configured for agent type: " + agent.Type,
		})
		return
	}

	// Create task in database
	task, err := h.taskRepo.Create(agent.ID, req.Action, req.Input, req.Priority, req.UserID)
	if err != nil {
		log.Printf("[AgentsHandler] Error creating task: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Execute tool asynchronously
	go func() {
		// Update status to processing
		h.taskRepo.UpdateStatus(task.ID, models.TaskStatusProcessing)

		// Create context with timeout
		ctx, cancel := context.WithTimeout(context.Background(), tool.Timeout)
		defer cancel()

		// Prepare input for CLI tool
		cliInput := map[string]any{
			"action":  req.Action,
			"task_id": task.ID,
		}
		for k, v := range req.Input {
			cliInput[k] = v
		}
		log.Printf("[AgentsHandler] Executing task %s with input keys: %+v", task.ID, cliInput)

		// Execute the tool
		result, err := h.executor.Execute(ctx, tool, cliInput)
		if err != nil {
			log.Printf("[AgentsHandler] Tool execution error for task %s: %v", task.ID, err)
			h.taskRepo.UpdateFailed(task.ID, err.Error())
			return
		}

		// Update task based on result
		if result.Status == "failed" {
			h.taskRepo.UpdateFailed(task.ID, result.Error)
		} else {
			h.taskRepo.UpdateCompleted(task.ID, result.Output)
		}
	}()

	// Return task immediately (async pattern)
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    task,
		"message": "Task enqueued successfully",
	})
}

// Update updates an agent
// PUT /api/agents/:id
func (h *AgentsHandler) Update(c *gin.Context) {
	id := c.Param("id")

	var updates map[string]any
	if err := c.ShouldBindJSON(&updates); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	agent, err := h.agentRepo.Update(id, updates)
	if err != nil {
		log.Printf("[AgentsHandler] Error updating agent %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if agent == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Agent not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    agent,
	})
}

// GetMetrics returns metrics for an agent
// GET /api/agents/:id/metrics
func (h *AgentsHandler) GetMetrics(c *gin.Context) {
	id := c.Param("id")

	// Verify agent exists
	agent, err := h.agentRepo.FindByID(id)
	if err != nil {
		log.Printf("[AgentsHandler] Error fetching agent %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	if agent == nil {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Agent not found",
		})
		return
	}

	// Get status counts
	statusCounts, err := h.taskRepo.GetStatusCounts(id)
	if err != nil {
		log.Printf("[AgentsHandler] Error fetching status counts: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Get recent tasks
	recentTasks, _, err := h.taskRepo.FindAll(map[string]any{
		"agentId": id,
		"limit":   10,
	})
	if err != nil {
		log.Printf("[AgentsHandler] Error fetching recent tasks: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Calculate total tasks
	total := 0
	for _, count := range statusCounts {
		total += count
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"statusCounts": statusCounts,
			"recentTasks":  recentTasks,
			"totalTasks":   total,
		},
	})
}
