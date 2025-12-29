package tools

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
)

// Executor manages CLI tool execution with hybrid concurrency control
type Executor struct {
	globalSemaphore  chan struct{}            // Global concurrency limit
	toolSemaphores   map[string]chan struct{} // Per-tool concurrency limits
	mu               sync.RWMutex
	defaultToolLimit int
	projectRoot      string
}

// NewExecutor creates an executor with hybrid concurrency control
func NewExecutor(globalLimit, defaultToolLimit int, projectRoot string) *Executor {
	return &Executor{
		globalSemaphore:  make(chan struct{}, globalLimit),
		toolSemaphores:   make(map[string]chan struct{}),
		defaultToolLimit: defaultToolLimit,
		projectRoot:      projectRoot,
	}
}

// getToolSemaphore returns or creates a per-tool semaphore
func (e *Executor) getToolSemaphore(toolName string, limit int) chan struct{} {
	e.mu.RLock()
	sem, exists := e.toolSemaphores[toolName]
	e.mu.RUnlock()

	if exists {
		return sem
	}

	e.mu.Lock()
	defer e.mu.Unlock()

	// Double-check after acquiring write lock
	if sem, exists := e.toolSemaphores[toolName]; exists {
		return sem
	}

	// Create new semaphore
	if limit <= 0 {
		limit = e.defaultToolLimit
	}
	sem = make(chan struct{}, limit)
	e.toolSemaphores[toolName] = sem
	return sem
}

// ExecuteInput is the standard input format for CLI tools
type ExecuteInput struct {
	Action string         `json:"action"`
	Input  map[string]any `json:"input"`
}

// ExecuteOutput is the standard output format from CLI tools
type ExecuteOutput struct {
	Status   string         `json:"status"`
	Output   map[string]any `json:"output,omitempty"`
	Error    string         `json:"error,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// Execute runs a CLI tool with the given input
// It applies both global and per-tool concurrency limits
func (e *Executor) Execute(ctx context.Context, tool ToolConfig, input map[string]any) (*ExecuteOutput, error) {
	toolSem := e.getToolSemaphore(tool.Name, tool.ConcurrencyLimit)

	// Acquire per-tool semaphore first
	select {
	case toolSem <- struct{}{}:
		defer func() { <-toolSem }()
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	// Then acquire global semaphore
	select {
	case e.globalSemaphore <- struct{}{}:
		defer func() { <-e.globalSemaphore }()
	case <-ctx.Done():
		return nil, ctx.Err()
	}

	log.Printf("[Executor] Starting tool: %s", tool.Name)

	// Marshal input to JSON
	inputJSON, err := json.Marshal(input)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal input: %w", err)
	}

	// Build command
	args := append(tool.Args, "--input", string(inputJSON))

	// Create context with timeout
	execCtx := ctx
	if tool.Timeout > 0 {
		var cancel context.CancelFunc
		execCtx, cancel = context.WithTimeout(ctx, tool.Timeout)
		defer cancel()
	}

	cmd := exec.CommandContext(execCtx, tool.Command, args...)

	// Set working directory
	workDir := tool.WorkingDir
	if workDir == "." || workDir == "" {
		workDir = e.projectRoot
	} else if !filepath.IsAbs(workDir) {
		workDir = filepath.Join(e.projectRoot, workDir)
	}
	cmd.Dir = workDir

	// Set environment variables
	cmd.Env = append(os.Environ(),
		"LLM_PROVIDER="+os.Getenv("LLM_PROVIDER"),
		"OPENAI_API_KEY="+os.Getenv("OPENAI_API_KEY"),
		"ANTHROPIC_API_KEY="+os.Getenv("ANTHROPIC_API_KEY"),
	)

	// Capture stdout and stderr
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	// Run command
	err = cmd.Run()

	// Log stderr (this is where Python logs go)
	if stderr.Len() > 0 {
		log.Printf("[Executor] %s stderr:\n%s", tool.Name, stderr.String())
	}

	if err != nil {
		// Check for context deadline exceeded
		if execCtx.Err() == context.DeadlineExceeded {
			return nil, fmt.Errorf("tool execution timed out after %v", tool.Timeout)
		}

		// Return error with stderr content for debugging
		errMsg := err.Error()
		if stderr.Len() > 0 {
			errMsg = stderr.String()
		}
		return &ExecuteOutput{
			Status: "failed",
			Error:  errMsg,
		}, nil
	}

	// Parse stdout as JSON
	var result ExecuteOutput
	if err := json.Unmarshal(stdout.Bytes(), &result); err != nil {
		// If output isn't valid JSON, wrap it
		return &ExecuteOutput{
			Status: "completed",
			Output: map[string]any{
				"raw_output": stdout.String(),
			},
		}, nil
	}

	log.Printf("[Executor] Tool %s completed with status: %s", tool.Name, result.Status)
	return &result, nil
}

// GetStats returns current executor statistics
func (e *Executor) GetStats() map[string]any {
	e.mu.RLock()
	defer e.mu.RUnlock()

	globalUsed := len(e.globalSemaphore)
	globalCap := cap(e.globalSemaphore)

	toolStats := make(map[string]map[string]int)
	for name, sem := range e.toolSemaphores {
		toolStats[name] = map[string]int{
			"used":     len(sem),
			"capacity": cap(sem),
		}
	}

	return map[string]any{
		"global": map[string]int{
			"used":     globalUsed,
			"capacity": globalCap,
		},
		"tools": toolStats,
	}
}
