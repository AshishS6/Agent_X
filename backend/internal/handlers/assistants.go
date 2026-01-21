package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
)

// AssistantsHandler handles assistant-related HTTP requests
type AssistantsHandler struct {
	projectRoot string
}

// NewAssistantsHandler creates a new assistants handler
func NewAssistantsHandler(projectRoot string) *AssistantsHandler {
	return &AssistantsHandler{
		projectRoot: projectRoot,
	}
}

// ChatRequest is the request body for assistant chat
type ChatRequest struct {
	Message       string `json:"message" binding:"required"`
	KnowledgeBase string `json:"knowledge_base"`
	Assistant     string `json:"assistant" binding:"required"`
}

// ChatResponse is the response from assistant chat
type ChatResponse struct {
	Assistant string                 `json:"assistant"`
	Answer    string                 `json:"answer"`
	Citations []string               `json:"citations"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// Chat handles assistant chat requests
// POST /api/assistants/:name/chat
func (h *AssistantsHandler) Chat(c *gin.Context) {
	assistantName := c.Param("name")

	// Parse request body
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Invalid request body: " + err.Error(),
		})
		return
	}

	// Use assistant name from path if not provided in body
	if req.Assistant == "" {
		req.Assistant = assistantName
	}

	// Set default knowledge base
	if req.KnowledgeBase == "" {
		req.KnowledgeBase = req.Assistant
	}

	log.Printf("[AssistantsHandler] Chat request - Assistant: %s, KB: %s", req.Assistant, req.KnowledgeBase)

	// Prepare input for Python runner
	input := map[string]interface{}{
		"message":        req.Message,
		"assistant":      req.Assistant,
		"knowledge_base": req.KnowledgeBase,
	}

	inputJSON, err := json.Marshal(input)
	if err != nil {
		log.Printf("[AssistantsHandler] Error marshaling input: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to prepare request",
		})
		return
	}

	// Create context with timeout (5 minutes for LLM calls)
	ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Minute)
	defer cancel()

	// Build Python command
	runnerPath := filepath.Join(h.projectRoot, "backend", "assistants", "runner.py")
	cmd := exec.CommandContext(ctx, "python3", runnerPath, "--input", string(inputJSON))

	// Set working directory
	cmd.Dir = filepath.Join(h.projectRoot, "backend")

	// Set environment variables
	cmd.Env = append(os.Environ(),
		"OLLAMA_BASE_URL="+os.Getenv("OLLAMA_BASE_URL"),
		"PYTHONPATH="+filepath.Join(h.projectRoot, "backend"),
	)

	// Capture stdout and stderr separately
	// stdout should contain ONLY JSON, stderr contains logs
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	// Run command
	err = cmd.Run()

	// Log stderr (Python logs) for debugging
	if stderr.Len() > 0 {
		log.Printf("[AssistantsHandler] Python runner stderr:\n%s", stderr.String())
	}

	if err != nil {
		log.Printf("[AssistantsHandler] Python runner error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   fmt.Sprintf("Assistant execution failed: %v", err),
		})
		return
	}

	// Parse JSON response from Python (stdout only)
	var response ChatResponse
	stdoutBytes := stdout.Bytes()
	if err := json.Unmarshal(stdoutBytes, &response); err != nil {
		log.Printf("[AssistantsHandler] Error parsing Python response: %v", err)
		previewLen := 500
		if len(stdoutBytes) < previewLen {
			previewLen = len(stdoutBytes)
		}
		log.Printf("[AssistantsHandler] Python stdout (first %d chars): %s", previewLen, string(stdoutBytes[:previewLen]))
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to parse assistant response",
		})
		return
	}

	// Check for error in metadata
	if errorMsg, ok := response.Metadata["error"].(string); ok && errorMsg != "" {
		log.Printf("[AssistantsHandler] Assistant returned error: %s", errorMsg)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   errorMsg,
		})
		return
	}

	// Return successful response
	c.JSON(http.StatusOK, response)
}
