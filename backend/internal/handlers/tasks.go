package handlers

import (
	"log"
	"net/http"
	"strconv"

	"go-backend/internal/models"

	"github.com/gin-gonic/gin"
)

// TasksHandler handles task-related HTTP requests
type TasksHandler struct {
	taskRepo *models.TaskRepository
}

// NewTasksHandler creates a new tasks handler
func NewTasksHandler() *TasksHandler {
	return &TasksHandler{
		taskRepo: models.NewTaskRepository(),
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
