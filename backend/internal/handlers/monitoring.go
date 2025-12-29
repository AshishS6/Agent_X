package handlers

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"runtime"
	"strings"
	"time"

	"go-backend/internal/database"
	"go-backend/internal/models"
	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

// MonitoringHandler handles monitoring-related HTTP requests
type MonitoringHandler struct {
	taskRepo  *models.TaskRepository
	agentRepo *models.AgentRepository
	executor  *tools.Executor
}

// NewMonitoringHandler creates a new monitoring handler
func NewMonitoringHandler(executor *tools.Executor) *MonitoringHandler {
	return &MonitoringHandler{
		taskRepo:  models.NewTaskRepository(),
		agentRepo: models.NewAgentRepository(),
		executor:  executor,
	}
}

// Health returns health status of the system
// GET /api/monitoring/health
func (h *MonitoringHandler) Health(c *gin.Context) {
	dbHealthy := database.Ping()

	status := "healthy"
	if !dbHealthy {
		status = "degraded"
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"status": status,
			"services": gin.H{
				"database": dbHealthy,
				"api":      true,
			},
			"executor": h.executor.GetStats(),
		},
	})
}

// Metrics returns system metrics
// GET /api/monitoring/metrics
func (h *MonitoringHandler) Metrics(c *gin.Context) {
	// Get agent counts
	agents, err := h.agentRepo.FindAll()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	activeAgents := 0
	for _, agent := range agents {
		if agent.Status == models.AgentStatusActive {
			activeAgents++
		}
	}

	// Get task counts
	statusCounts, err := h.taskRepo.GetStatusCounts("")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Get recent activity
	recentTasks, _, err := h.taskRepo.FindAll(map[string]any{
		"limit": 20,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// Calculate efficiency metrics (simplified)
	totalTasks := statusCounts["completed"] + statusCounts["failed"]
	efficiencyScore := 0.0
	if totalTasks > 0 {
		efficiencyScore = float64(statusCounts["completed"]) / float64(totalTasks) * 100
	}

	// Estimate time saved (rough calculation: 5 minutes per completed task)
	timeSavedHours := float64(statusCounts["completed"]) * 5.0 / 60.0

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"activeAgents": gin.H{
				"value": activeAgents,
				"count": activeAgents,
				"total": len(agents),
			},
			"tasksCompleted": gin.H{
				"value": statusCounts["completed"],
				"trend": 0,
			},
			"timeSaved": gin.H{
				"value": timeSavedHours,
				"hours": timeSavedHours,
			},
			"efficiencyScore": gin.H{
				"value": efficiencyScore,
				"score": efficiencyScore,
			},
			"taskBreakdown": statusCounts,
			"recentActivity": gin.H{
				"tasks": recentTasks,
			},
			"executor": h.executor.GetStats(),
		},
	})
}

// Activity returns recent system activity
// GET /api/monitoring/activity
func (h *MonitoringHandler) Activity(c *gin.Context) {
	limit := 20
	if l := c.Query("limit"); l != "" {
		if _, err := c.GetQuery("limit"); err {
			limit = 20
		}
	}

	tasks, _, err := h.taskRepo.FindAll(map[string]any{
		"limit": limit,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    tasks,
	})
}

// System returns system information
// GET /api/monitoring/system
func (h *MonitoringHandler) System(c *gin.Context) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"runtime": gin.H{
				"goroutines": runtime.NumGoroutine(),
				"cpus":       runtime.NumCPU(),
				"goVersion":  runtime.Version(),
			},
			"memory": gin.H{
				"allocMB":      m.Alloc / 1024 / 1024,
				"totalAllocMB": m.TotalAlloc / 1024 / 1024,
				"sysMB":        m.Sys / 1024 / 1024,
				"numGC":        m.NumGC,
			},
			"executor": h.executor.GetStats(),
		},
	})
}

// Proxy fetches external URLs for iframe preview
// GET /api/monitoring/proxy?url=https://example.com
func (h *MonitoringHandler) Proxy(c *gin.Context) {
	targetURL := c.Query("url")
	if targetURL == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Missing 'url' query parameter",
		})
		return
	}

	// Parse the target URL to get base URL for relative path resolution
	parsedURL, err := url.Parse(targetURL)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid URL: " + err.Error(),
		})
		return
	}
	baseURL := parsedURL.Scheme + "://" + parsedURL.Host

	// Create HTTP client with timeout
	client := &http.Client{
		Timeout: 15 * time.Second,
	}

	// Create request with browser-like headers
	req, err := http.NewRequest("GET", targetURL, nil)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid URL: " + err.Error(),
		})
		return
	}

	// Set headers to mimic a browser
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.9")

	// Fetch the URL
	resp, err := client.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"success": false,
			"error":   "Failed to fetch URL: " + err.Error(),
		})
		return
	}
	defer resp.Body.Close()

	// Read body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to read response: " + err.Error(),
		})
		return
	}

	// Get content type from response
	contentType := resp.Header.Get("Content-Type")
	if contentType == "" {
		contentType = "text/html; charset=utf-8"
	}

	// For HTML content, inject a <base> tag to resolve relative URLs
	if strings.Contains(contentType, "text/html") {
		htmlContent := string(body)

		// Add base tag right after <head> to resolve relative URLs (matching Node.js exactly)
		baseTag := fmt.Sprintf(`<base href="%s/">`, baseURL)

		// Try to inject after <head> (matching Node.js logic)
		if strings.Contains(htmlContent, "<head>") {
			htmlContent = strings.Replace(htmlContent, "<head>", "<head>\n    "+baseTag, 1)
		} else if strings.Contains(htmlContent, "<html>") {
			htmlContent = strings.Replace(htmlContent, "<html>", "<html>\n<head>\n    "+baseTag+"\n</head>", 1)
		} else {
			// Fallback: prepend to body
			htmlContent = baseTag + htmlContent
		}

		body = []byte(htmlContent)
	}

	// Set response headers for iframe compatibility
	c.Header("Content-Type", contentType)
	c.Header("X-Frame-Options", "ALLOWALL")
	c.Header("Content-Security-Policy", "frame-ancestors *")
	// Remove any existing CSP that might block resources
	c.Header("Access-Control-Allow-Origin", "*")

	c.Data(resp.StatusCode, contentType, body)
}
