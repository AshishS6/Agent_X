package handlers

import (
	"net/http"

	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

// ToolsHandler handles tool-related HTTP requests
type ToolsHandler struct{}

// NewToolsHandler creates a new tools handler
func NewToolsHandler() *ToolsHandler {
	return &ToolsHandler{}
}

// ListTools returns all available tools
// GET /api/tools
func (h *ToolsHandler) ListTools(c *gin.Context) {
	toolList := tools.ListTools()

	// Convert to API-friendly format
	result := make([]gin.H, len(toolList))
	for i, tool := range toolList {
		result[i] = gin.H{
			"name":        tool.AgentType,
			"displayName": tool.Name,
			"description": tool.Description,
			"timeout":     tool.Timeout.String(),
			"concurrency": tool.ConcurrencyLimit,
		}
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    result,
	})
}

// GetTool returns a specific tool's configuration
// GET /api/tools/:name
func (h *ToolsHandler) GetTool(c *gin.Context) {
	name := c.Param("name")

	tool, exists := tools.GetTool(name)
	if !exists {
		// Try by agent type
		tool, exists = tools.GetToolByAgentType(name)
	}

	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Tool not found: " + name,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"name":        tool.AgentType,
			"displayName": tool.Name,
			"description": tool.Description,
			"timeout":     tool.Timeout.String(),
			"concurrency": tool.ConcurrencyLimit,
		},
	})
}
