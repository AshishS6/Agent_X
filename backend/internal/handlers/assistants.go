package handlers

import (
	"bufio"
	"context"
	"encoding/json"
	"io"
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

// Chat handles assistant chat requests with streaming response (NDJSON)
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

	log.Printf("[AssistantsHandler] Chat stream request - Assistant: %s, KB: %s", req.Assistant, req.KnowledgeBase)

	// Prepare input for Python runner
	input := map[string]interface{}{
		"message":        req.Message,
		"assistant":      req.Assistant,
		"knowledge_base": req.KnowledgeBase,
	}

	inputJSON, err := json.Marshal(input)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to prepare request",
		})
		return
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(c.Request.Context(), 10*time.Minute)
	defer cancel()

	// Build Python command
	runnerPath := filepath.Join(h.projectRoot, "backend", "assistants", "runner.py")
	cmd := exec.CommandContext(ctx, "python3", runnerPath, "--input", string(inputJSON))
	cmd.Dir = filepath.Join(h.projectRoot, "backend")
	cmd.Env = append(os.Environ(),
		"LLM_MODE="+os.Getenv("LLM_MODE"),
		"LLM_PRIORITY="+os.Getenv("LLM_PRIORITY"),
		"LLM_FALLBACK_ENABLED="+os.Getenv("LLM_FALLBACK_ENABLED"),
		"LLM_LOCAL_MODEL="+os.Getenv("LLM_LOCAL_MODEL"),
		"LLM_CLOUD_MODEL="+os.Getenv("LLM_CLOUD_MODEL"),
		"OLLAMA_BASE_URL="+os.Getenv("OLLAMA_BASE_URL"),
		"OPENAI_API_KEY="+os.Getenv("OPENAI_API_KEY"),
		"ANTHROPIC_API_KEY="+os.Getenv("ANTHROPIC_API_KEY"),
		"PYTHONPATH="+filepath.Join(h.projectRoot, "backend"),
		"PYTHONUNBUFFERED=1", // Ensure Python flushes stdout immediately
	)

	// Get stdout pipe
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create stdout pipe"})
		return
	}

	// Capture stderr for debugging
	stderrReader, err := cmd.StderrPipe()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create stderr pipe"})
		return
	}

	// Start command
	if err := cmd.Start(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Failed to start assistant",
		})
		return
	}

	// Stream logs from stderr in background
	go func() {
		scanner := bufio.NewScanner(stderrReader)
		for scanner.Scan() {
			log.Printf("[Python Log] %s", scanner.Text())
		}
	}()

	// Set headers for streaming
	c.Writer.Header().Set("Content-Type", "application/x-ndjson")
	c.Writer.Header().Set("Transfer-Encoding", "chunked")
	c.Writer.Header().Set("Cache-Control", "no-cache")
	c.Writer.WriteHeader(http.StatusOK)

	// Stream stdout line by line
	reader := bufio.NewReader(stdout)
	for {
		line, err := reader.ReadBytes('\n')
		if len(line) > 0 {
			c.Writer.Write(line)
			c.Writer.Flush()
		}
		if err != nil {
			if err != io.EOF {
				log.Printf("Error reading stream: %v", err)
			}
			break
		}
	}

	// Wait for command to finish
	if err := cmd.Wait(); err != nil {
		log.Printf("[AssistantsHandler] Python runner error: %v", err)
	}
}
