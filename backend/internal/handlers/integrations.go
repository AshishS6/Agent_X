package handlers

import (
	"log"
	"net/http"

	"go-backend/internal/models"

	"github.com/gin-gonic/gin"
)

type IntegrationsHandler struct {
	repo *models.IntegrationRepository
}

func NewIntegrationsHandler() *IntegrationsHandler {
	return &IntegrationsHandler{
		repo: models.NewIntegrationRepository(),
	}
}

type CreateIntegrationRequest struct {
	Name     string         `json:"name" binding:"required"`
	Type     string         `json:"type" binding:"required"`
	Status   string         `json:"status"`
	Config   map[string]any `json:"config"`
	LastSync any            `json:"last_sync"`
}

// GetAll returns all integrations
// GET /api/integrations
func (h *IntegrationsHandler) GetAll(c *gin.Context) {
	items, err := h.repo.FindAll()
	if err != nil {
		log.Printf("[IntegrationsHandler] Error fetching integrations: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": items})
}

// Create creates an integration row
// POST /api/integrations
func (h *IntegrationsHandler) Create(c *gin.Context) {
	var req CreateIntegrationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": err.Error()})
		return
	}

	status := models.IntegrationStatusDisconnected
	if req.Status != "" {
		status = models.IntegrationStatus(req.Status)
	}
	if req.Config == nil {
		req.Config = map[string]any{}
	}

	it, err := h.repo.Create(req.Name, req.Type, status, req.Config)
	if err != nil {
		log.Printf("[IntegrationsHandler] Error creating integration: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": it})
}

// Update updates an integration
// PUT /api/integrations/:id
func (h *IntegrationsHandler) Update(c *gin.Context) {
	id := c.Param("id")

	var updates map[string]any
	if err := c.ShouldBindJSON(&updates); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"success": false, "error": err.Error()})
		return
	}

	it, err := h.repo.Update(id, updates)
	if err != nil {
		log.Printf("[IntegrationsHandler] Error updating integration %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}
	if it == nil {
		c.JSON(http.StatusNotFound, gin.H{"success": false, "error": "Integration not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "data": it})
}

// Delete removes an integration
// DELETE /api/integrations/:id
func (h *IntegrationsHandler) Delete(c *gin.Context) {
	id := c.Param("id")

	if err := h.repo.Delete(id); err != nil {
		log.Printf("[IntegrationsHandler] Error deleting integration %s: %v", id, err)
		c.JSON(http.StatusInternalServerError, gin.H{"success": false, "error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true})
}
