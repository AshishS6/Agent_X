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
// This contract is LOCKED - do not change without frontend coordination
type ChatResponse struct {
	Assistant string      `json:"assistant"`  // Required: assistant name
	Answer    string      `json:"answer"`     // Required: markdown-formatted answer
	Citations []string    `json:"citations"`  // Required: array of public URLs (empty if none)
	Metadata  ChatMetadata `json:"metadata"`  // Required: structured metadata
}

// ChatMetadata contains structured metadata about the response
type ChatMetadata struct {
	Model     string `json:"model"`      // LLM model used
	Provider  string `json:"provider"`  // LLM provider (ollama, openai, etc.)
	RagUsed   bool   `json:"rag_used"`  // Whether RAG context was used
	KB        string `json:"kb"`        // Knowledge base name (empty if no RAG)
	LatencyMs int64  `json:"latency_ms"` // Request latency in milliseconds
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

	// Record start time for latency measurement
	startTime := time.Now()

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
	// First parse as map to handle flexible Python response
	var rawResponse map[string]interface{}
	stdoutBytes := stdout.Bytes()
	if err := json.Unmarshal(stdoutBytes, &rawResponse); err != nil {
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
	rawMetadata, _ := rawResponse["metadata"].(map[string]interface{})
	if errorMsg, ok := rawMetadata["error"].(string); ok && errorMsg != "" {
		log.Printf("[AssistantsHandler] Assistant returned error: %s", errorMsg)
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   errorMsg,
		})
		return
	}

	// Extract and validate required fields
	answer, _ := rawResponse["answer"].(string)
	if answer == "" {
		log.Printf("[AssistantsHandler] Assistant returned empty answer")
		c.JSON(http.StatusInternalServerError, gin.H{
			"success": false,
			"error":   "Assistant returned empty answer",
		})
		return
	}

	assistant, _ := rawResponse["assistant"].(string)
	if assistant == "" {
		assistant = req.Assistant
	}

	// Ensure citations is always an array (never null)
	var citations []string
	if rawCitations, ok := rawResponse["citations"].([]interface{}); ok {
		citations = make([]string, 0, len(rawCitations))
		for _, cit := range rawCitations {
			if str, ok := cit.(string); ok {
				citations = append(citations, str)
			}
		}
	}
	if citations == nil {
		citations = []string{}
	}

	// Calculate latency
	latencyMs := time.Since(startTime).Milliseconds()

	// Build normalized metadata
	normalizedMetadata := ChatMetadata{
		Model:     getStringFromMap(rawMetadata, "model", ""),
		Provider:  getStringFromMap(rawMetadata, "provider", "ollama"),
		RagUsed:   getBoolFromMap(rawMetadata, "rag_used", false),
		KB:        req.KnowledgeBase,
		LatencyMs: latencyMs,
	}

	// Build final response with locked contract
	response := ChatResponse{
		Assistant: assistant,
		Answer:    answer,
		Citations: citations,
		Metadata:  normalizedMetadata,
	}

	// Log observability metrics
	log.Printf("[AssistantsHandler] ✅ Assistant: %s, KB: %s, RAG: %v, Latency: %dms, Answer length: %d chars, Citations: %d",
		response.Assistant,
		normalizedMetadata.KB,
		normalizedMetadata.RagUsed,
		normalizedMetadata.LatencyMs,
		len(response.Answer),
		len(response.Citations),
	)

	// Return successful response
	c.JSON(http.StatusOK, response)
}

// Helper functions for metadata extraction
func getStringFromMap(m map[string]interface{}, key string, defaultValue string) string {
	if val, ok := m[key]; ok {
		if str, ok := val.(string); ok {
			return str
		}
	}
	return defaultValue
}

func getBoolFromMap(m map[string]interface{}, key string, defaultValue bool) bool {
	if val, ok := m[key]; ok {
		if b, ok := val.(bool); ok {
			return b
		}
	}
	return defaultValue
}
