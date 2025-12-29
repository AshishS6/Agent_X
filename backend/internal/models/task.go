package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"go-backend/internal/database"

	"github.com/google/uuid"
)

type TaskStatus string

const (
	TaskStatusPending    TaskStatus = "pending"
	TaskStatusProcessing TaskStatus = "processing"
	TaskStatusCompleted  TaskStatus = "completed"
	TaskStatusFailed     TaskStatus = "failed"
)

type TaskPriority string

const (
	TaskPriorityHigh   TaskPriority = "high"
	TaskPriorityMedium TaskPriority = "medium"
	TaskPriorityLow    TaskPriority = "low"
)

type Task struct {
	ID          string          `json:"id"`
	AgentID     string          `json:"agent_id"`
	UserID      *string         `json:"user_id,omitempty"`
	Action      string          `json:"action"`
	Input       json.RawMessage `json:"input"`
	Output      json.RawMessage `json:"output,omitempty"`
	Status      TaskStatus      `json:"status"`
	Priority    TaskPriority    `json:"priority"`
	Error       *string         `json:"error,omitempty"`
	StartedAt   *time.Time      `json:"started_at,omitempty"`
	CompletedAt *time.Time      `json:"completed_at,omitempty"`
	CreatedAt   time.Time       `json:"created_at"`
}

type TaskRepository struct{}

func NewTaskRepository() *TaskRepository {
	return &TaskRepository{}
}

func (r *TaskRepository) Create(agentID, action string, input map[string]any, priority, userID string) (*Task, error) {
	id := uuid.New().String()
	inputJSON, err := json.Marshal(input)
	if err != nil {
		return nil, err
	}

	var userIDPtr *string
	if userID != "" {
		userIDPtr = &userID
	}

	query := `
		INSERT INTO tasks (id, agent_id, user_id, action, input, status, priority)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id, agent_id, user_id, action, input, status, priority, created_at
	`

	task := &Task{}
	err = database.DB.QueryRow(query, id, agentID, userIDPtr, action, inputJSON, TaskStatusPending, priority).Scan(
		&task.ID, &task.AgentID, &task.UserID, &task.Action, &task.Input, &task.Status, &task.Priority, &task.CreatedAt,
	)
	if err != nil {
		return nil, err
	}

	return task, nil
}

func (r *TaskRepository) FindByID(id string) (*Task, error) {
	query := `
		SELECT id, agent_id, user_id, action, input, output, status, priority, error, started_at, completed_at, created_at
		FROM tasks WHERE id = $1
	`

	task := &Task{}
	var output, errorMsg sql.NullString
	var startedAt, completedAt sql.NullTime

	err := database.DB.QueryRow(query, id).Scan(
		&task.ID, &task.AgentID, &task.UserID, &task.Action, &task.Input,
		&output, &task.Status, &task.Priority, &errorMsg, &startedAt, &completedAt, &task.CreatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if output.Valid {
		task.Output = json.RawMessage(output.String)
	}
	if errorMsg.Valid {
		task.Error = &errorMsg.String
	}
	if startedAt.Valid {
		task.StartedAt = &startedAt.Time
	}
	if completedAt.Valid {
		task.CompletedAt = &completedAt.Time
	}

	return task, nil
}

func (r *TaskRepository) FindAll(filters map[string]any) ([]Task, int, error) {
	query := `SELECT id, agent_id, user_id, action, input, output, status, priority, error, started_at, completed_at, created_at FROM tasks WHERE 1=1`
	countQuery := `SELECT COUNT(*)::int FROM tasks WHERE 1=1`
	args := []any{}
	argCount := 1

	if agentID, ok := filters["agentId"].(string); ok && agentID != "" {
		query += ` AND agent_id = $` + string(rune('0'+argCount))
		countQuery += ` AND agent_id = $` + string(rune('0'+argCount))
		args = append(args, agentID)
		argCount++
	}

	if status, ok := filters["status"].(string); ok && status != "" {
		query += ` AND status = $` + string(rune('0'+argCount))
		countQuery += ` AND status = $` + string(rune('0'+argCount))
		args = append(args, status)
		argCount++
	}

	query += ` ORDER BY created_at DESC`

	limit := 50
	offset := 0
	if l, ok := filters["limit"].(int); ok && l > 0 {
		limit = l
	}
	if o, ok := filters["offset"].(int); ok && o > 0 {
		offset = o
	}

	query += ` LIMIT $` + string(rune('0'+argCount))
	args = append(args, limit)
	argCount++

	query += ` OFFSET $` + string(rune('0'+argCount))
	args = append(args, offset)

	// Get total count
	var total int
	countArgs := args[:len(args)-2] // Exclude limit and offset
	err := database.DB.QueryRow(countQuery, countArgs...).Scan(&total)
	if err != nil {
		return nil, 0, err
	}

	// Get tasks
	rows, err := database.DB.Query(query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	tasks := []Task{}
	for rows.Next() {
		task := Task{}
		var output, errorMsg sql.NullString
		var startedAt, completedAt sql.NullTime

		err := rows.Scan(
			&task.ID, &task.AgentID, &task.UserID, &task.Action, &task.Input,
			&output, &task.Status, &task.Priority, &errorMsg, &startedAt, &completedAt, &task.CreatedAt,
		)
		if err != nil {
			return nil, 0, err
		}

		if output.Valid {
			task.Output = json.RawMessage(output.String)
		}
		if errorMsg.Valid {
			task.Error = &errorMsg.String
		}
		if startedAt.Valid {
			task.StartedAt = &startedAt.Time
		}
		if completedAt.Valid {
			task.CompletedAt = &completedAt.Time
		}

		tasks = append(tasks, task)
	}

	return tasks, total, nil
}

func (r *TaskRepository) UpdateStatus(id string, status TaskStatus) error {
	query := `UPDATE tasks SET status = $1, started_at = NOW() WHERE id = $2`
	_, err := database.DB.Exec(query, status, id)
	return err
}

func (r *TaskRepository) UpdateCompleted(id string, output map[string]any) error {
	outputJSON, err := json.Marshal(output)
	if err != nil {
		return err
	}

	query := `UPDATE tasks SET status = $1, output = $2, completed_at = NOW() WHERE id = $3`
	_, err = database.DB.Exec(query, TaskStatusCompleted, outputJSON, id)
	return err
}

func (r *TaskRepository) UpdateFailed(id string, errorMsg string) error {
	query := `UPDATE tasks SET status = $1, error = $2, completed_at = NOW() WHERE id = $3`
	_, err := database.DB.Exec(query, TaskStatusFailed, errorMsg, id)
	return err
}

func (r *TaskRepository) GetStatusCounts(agentID string) (map[string]int, error) {
	query := `SELECT status, COUNT(*)::int FROM tasks`
	args := []any{}

	if agentID != "" {
		query += ` WHERE agent_id = $1`
		args = append(args, agentID)
	}

	query += ` GROUP BY status`

	rows, err := database.DB.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	counts := map[string]int{
		"pending":    0,
		"processing": 0,
		"completed":  0,
		"failed":     0,
	}

	for rows.Next() {
		var status string
		var count int
		if err := rows.Scan(&status, &count); err != nil {
			return nil, err
		}
		counts[status] = count
	}

	return counts, nil
}
