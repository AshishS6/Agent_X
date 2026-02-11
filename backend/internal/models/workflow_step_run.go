package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"go-backend/internal/database"

	"github.com/google/uuid"
)

type WorkflowStepRunStatus string

const (
	WorkflowStepRunStatusRunning   WorkflowStepRunStatus = "running"
	WorkflowStepRunStatusCompleted WorkflowStepRunStatus = "completed"
	WorkflowStepRunStatusFailed    WorkflowStepRunStatus = "failed"
	WorkflowStepRunStatusSkipped   WorkflowStepRunStatus = "skipped"
)

type WorkflowStepRun struct {
	ID            string                `json:"id"`
	WorkflowRunID string                `json:"workflow_run_id"`
	StepIndex     int                   `json:"step_index"`
	StepType      string                `json:"step_type"`
	Status        WorkflowStepRunStatus `json:"status"`
	Input         json.RawMessage       `json:"input"`
	Output        json.RawMessage       `json:"output"`
	TaskID        *string               `json:"task_id,omitempty"`
	Error         *string               `json:"error,omitempty"`
	StartedAt     time.Time             `json:"started_at"`
	CompletedAt   *time.Time            `json:"completed_at,omitempty"`
}

type WorkflowStepRunRepository struct{}

func NewWorkflowStepRunRepository() *WorkflowStepRunRepository {
	return &WorkflowStepRunRepository{}
}

func (r *WorkflowStepRunRepository) Create(workflowRunID string, stepIndex int, stepType string, input any) (*WorkflowStepRun, error) {
	id := uuid.New().String()
	inputJSON, _ := json.Marshal(input)

	query := `
		INSERT INTO workflow_step_runs (id, workflow_run_id, step_index, step_type, status, input, output)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id, workflow_run_id, step_index, step_type, status, input, output, task_id, error, started_at, completed_at
	`

	step := &WorkflowStepRun{}
	var inputStr sql.NullString
	var outputStr sql.NullString
	var taskID sql.NullString
	var errMsg sql.NullString
	var completedAt sql.NullTime

	emptyOutput := []byte(`{}`)
	err := database.DB.QueryRow(query, id, workflowRunID, stepIndex, stepType, WorkflowStepRunStatusRunning, inputJSON, emptyOutput).Scan(
		&step.ID,
		&step.WorkflowRunID,
		&step.StepIndex,
		&step.StepType,
		&step.Status,
		&inputStr,
		&outputStr,
		&taskID,
		&errMsg,
		&step.StartedAt,
		&completedAt,
	)
	if err != nil {
		return nil, err
	}

	if inputStr.Valid {
		step.Input = json.RawMessage(inputStr.String)
	} else {
		step.Input = json.RawMessage("{}")
	}
	if outputStr.Valid {
		step.Output = json.RawMessage(outputStr.String)
	} else {
		step.Output = json.RawMessage("{}")
	}
	if taskID.Valid {
		step.TaskID = &taskID.String
	}
	if errMsg.Valid {
		step.Error = &errMsg.String
	}
	if completedAt.Valid {
		step.CompletedAt = &completedAt.Time
	}

	return step, nil
}

func (r *WorkflowStepRunRepository) FindByRunID(workflowRunID string) ([]WorkflowStepRun, error) {
	query := `
		SELECT id, workflow_run_id, step_index, step_type, status, input, output, task_id, error, started_at, completed_at
		FROM workflow_step_runs
		WHERE workflow_run_id = $1
		ORDER BY step_index ASC
	`

	rows, err := database.DB.Query(query, workflowRunID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	steps := []WorkflowStepRun{}
	for rows.Next() {
		step := WorkflowStepRun{}
		var inputStr sql.NullString
		var outputStr sql.NullString
		var taskID sql.NullString
		var errMsg sql.NullString
		var completedAt sql.NullTime

		if err := rows.Scan(
			&step.ID,
			&step.WorkflowRunID,
			&step.StepIndex,
			&step.StepType,
			&step.Status,
			&inputStr,
			&outputStr,
			&taskID,
			&errMsg,
			&step.StartedAt,
			&completedAt,
		); err != nil {
			return nil, err
		}

		if inputStr.Valid {
			step.Input = json.RawMessage(inputStr.String)
		} else {
			step.Input = json.RawMessage("{}")
		}
		if outputStr.Valid {
			step.Output = json.RawMessage(outputStr.String)
		} else {
			step.Output = json.RawMessage("{}")
		}
		if taskID.Valid {
			step.TaskID = &taskID.String
		}
		if errMsg.Valid {
			step.Error = &errMsg.String
		}
		if completedAt.Valid {
			step.CompletedAt = &completedAt.Time
		}

		steps = append(steps, step)
	}

	return steps, nil
}

// UpdateCompleted marks step completed and persists output.
func (r *WorkflowStepRunRepository) UpdateCompleted(id string, output any, taskID *string) error {
	outputJSON, _ := json.Marshal(output)
	_, err := database.DB.Exec(
		`UPDATE workflow_step_runs SET status = $1, output = $2, task_id = $3, completed_at = NOW() WHERE id = $4`,
		WorkflowStepRunStatusCompleted,
		outputJSON,
		taskID,
		id,
	)
	return err
}

// UpdateFailed marks step failed and persists output (ALWAYS write output, even on failure).
func (r *WorkflowStepRunRepository) UpdateFailed(id string, output any, errMsg string, taskID *string) error {
	outputJSON, _ := json.Marshal(output)
	_, err := database.DB.Exec(
		`UPDATE workflow_step_runs SET status = $1, output = $2, error = $3, task_id = $4, completed_at = NOW() WHERE id = $5`,
		WorkflowStepRunStatusFailed,
		outputJSON,
		errMsg,
		taskID,
		id,
	)
	return err
}
