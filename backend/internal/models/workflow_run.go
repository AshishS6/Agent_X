package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"go-backend/internal/database"

	"github.com/google/uuid"
)

type WorkflowRunStatus string

const (
	WorkflowRunStatusRunning   WorkflowRunStatus = "running"
	WorkflowRunStatusCompleted WorkflowRunStatus = "completed"
	WorkflowRunStatusFailed    WorkflowRunStatus = "failed"
)

type WorkflowRun struct {
	ID              string            `json:"id"`
	WorkflowID      string            `json:"workflow_id"`
	Status          WorkflowRunStatus `json:"status"`
	CaseID          *string           `json:"case_id,omitempty"`
	ProviderEventID *string           `json:"provider_event_id,omitempty"`
	IdempotencyKey  *string           `json:"idempotency_key,omitempty"`
	TriggerPayload  json.RawMessage   `json:"trigger_payload"`
	StartedAt       time.Time         `json:"started_at"`
	CompletedAt     *time.Time        `json:"completed_at,omitempty"`
	Error           *string           `json:"error,omitempty"`
}

type WorkflowRunRepository struct{}

func NewWorkflowRunRepository() *WorkflowRunRepository {
	return &WorkflowRunRepository{}
}

func (r *WorkflowRunRepository) FindByID(id string) (*WorkflowRun, error) {
	query := `
		SELECT id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
		FROM workflow_runs
		WHERE id = $1
	`

	run := &WorkflowRun{}
	var caseID sql.NullString
	var providerEventID sql.NullString
	var idk sql.NullString
	var payload sql.NullString
	var completedAt sql.NullTime
	var errMsg sql.NullString

	err := database.DB.QueryRow(query, id).Scan(
		&run.ID,
		&run.WorkflowID,
		&run.Status,
		&caseID,
		&providerEventID,
		&idk,
		&payload,
		&run.StartedAt,
		&completedAt,
		&errMsg,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if caseID.Valid {
		run.CaseID = &caseID.String
	}
	if providerEventID.Valid {
		run.ProviderEventID = &providerEventID.String
	}
	if idk.Valid {
		run.IdempotencyKey = &idk.String
	}
	if payload.Valid {
		run.TriggerPayload = json.RawMessage(payload.String)
	} else {
		run.TriggerPayload = json.RawMessage("{}")
	}
	if completedAt.Valid {
		run.CompletedAt = &completedAt.Time
	}
	if errMsg.Valid {
		run.Error = &errMsg.String
	}

	return run, nil
}

func (r *WorkflowRunRepository) FindByWorkflowID(workflowID string, limit, offset int) ([]WorkflowRun, int, error) {
	countQuery := `SELECT COUNT(*)::int FROM workflow_runs WHERE workflow_id = $1`
	var total int
	if err := database.DB.QueryRow(countQuery, workflowID).Scan(&total); err != nil {
		return nil, 0, err
	}

	query := `
		SELECT id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
		FROM workflow_runs
		WHERE workflow_id = $1
		ORDER BY started_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := database.DB.Query(query, workflowID, limit, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	runs := []WorkflowRun{}
	for rows.Next() {
		run := WorkflowRun{}
		var caseID sql.NullString
		var providerEventID sql.NullString
		var idk sql.NullString
		var payload sql.NullString
		var completedAt sql.NullTime
		var errMsg sql.NullString

		if err := rows.Scan(
			&run.ID,
			&run.WorkflowID,
			&run.Status,
			&caseID,
			&providerEventID,
			&idk,
			&payload,
			&run.StartedAt,
			&completedAt,
			&errMsg,
		); err != nil {
			return nil, 0, err
		}

		if caseID.Valid {
			run.CaseID = &caseID.String
		}
		if providerEventID.Valid {
			run.ProviderEventID = &providerEventID.String
		}
		if idk.Valid {
			run.IdempotencyKey = &idk.String
		}
		if payload.Valid {
			run.TriggerPayload = json.RawMessage(payload.String)
		} else {
			run.TriggerPayload = json.RawMessage("{}")
		}
		if completedAt.Valid {
			run.CompletedAt = &completedAt.Time
		}
		if errMsg.Valid {
			run.Error = &errMsg.String
		}

		runs = append(runs, run)
	}

	return runs, total, nil
}

func (r *WorkflowRunRepository) FindAll(limit, offset int) ([]WorkflowRun, int, error) {
	countQuery := `SELECT COUNT(*)::int FROM workflow_runs`
	var total int
	if err := database.DB.QueryRow(countQuery).Scan(&total); err != nil {
		return nil, 0, err
	}

	query := `
		SELECT id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
		FROM workflow_runs
		ORDER BY started_at DESC
		LIMIT $1 OFFSET $2
	`

	rows, err := database.DB.Query(query, limit, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	runs := []WorkflowRun{}
	for rows.Next() {
		run := WorkflowRun{}
		var caseID sql.NullString
		var providerEventID sql.NullString
		var idk sql.NullString
		var payload sql.NullString
		var completedAt sql.NullTime
		var errMsg sql.NullString

		if err := rows.Scan(
			&run.ID,
			&run.WorkflowID,
			&run.Status,
			&caseID,
			&providerEventID,
			&idk,
			&payload,
			&run.StartedAt,
			&completedAt,
			&errMsg,
		); err != nil {
			return nil, 0, err
		}

		if caseID.Valid {
			run.CaseID = &caseID.String
		}
		if providerEventID.Valid {
			run.ProviderEventID = &providerEventID.String
		}
		if idk.Valid {
			run.IdempotencyKey = &idk.String
		}
		if payload.Valid {
			run.TriggerPayload = json.RawMessage(payload.String)
		} else {
			run.TriggerPayload = json.RawMessage("{}")
		}
		if completedAt.Valid {
			run.CompletedAt = &completedAt.Time
		}
		if errMsg.Valid {
			run.Error = &errMsg.String
		}

		runs = append(runs, run)
	}

	return runs, total, nil
}

func (r *WorkflowRunRepository) FindByIdempotencyKey(workflowID string, idempotencyKey string) (*WorkflowRun, error) {
	query := `
		SELECT id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
		FROM workflow_runs
		WHERE workflow_id = $1 AND idempotency_key = $2
		LIMIT 1
	`

	run := &WorkflowRun{}
	var caseID sql.NullString
	var providerEventID sql.NullString
	var idk sql.NullString
	var payload sql.NullString
	var completedAt sql.NullTime
	var errMsg sql.NullString

	err := database.DB.QueryRow(query, workflowID, idempotencyKey).Scan(
		&run.ID,
		&run.WorkflowID,
		&run.Status,
		&caseID,
		&providerEventID,
		&idk,
		&payload,
		&run.StartedAt,
		&completedAt,
		&errMsg,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if caseID.Valid {
		run.CaseID = &caseID.String
	}
	if providerEventID.Valid {
		run.ProviderEventID = &providerEventID.String
	}
	if idk.Valid {
		run.IdempotencyKey = &idk.String
	}
	if payload.Valid {
		run.TriggerPayload = json.RawMessage(payload.String)
	} else {
		run.TriggerPayload = json.RawMessage("{}")
	}
	if completedAt.Valid {
		run.CompletedAt = &completedAt.Time
	}
	if errMsg.Valid {
		run.Error = &errMsg.String
	}

	return run, nil
}

func (r *WorkflowRunRepository) FindByProviderEventID(workflowID string, providerEventID string) (*WorkflowRun, error) {
	query := `
		SELECT id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
		FROM workflow_runs
		WHERE workflow_id = $1 AND provider_event_id = $2
		LIMIT 1
	`

	run := &WorkflowRun{}
	var caseID sql.NullString
	var peid sql.NullString
	var idk sql.NullString
	var payload sql.NullString
	var completedAt sql.NullTime
	var errMsg sql.NullString

	err := database.DB.QueryRow(query, workflowID, providerEventID).Scan(
		&run.ID,
		&run.WorkflowID,
		&run.Status,
		&caseID,
		&peid,
		&idk,
		&payload,
		&run.StartedAt,
		&completedAt,
		&errMsg,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if caseID.Valid {
		run.CaseID = &caseID.String
	}
	if peid.Valid {
		run.ProviderEventID = &peid.String
	}
	if idk.Valid {
		run.IdempotencyKey = &idk.String
	}
	if payload.Valid {
		run.TriggerPayload = json.RawMessage(payload.String)
	} else {
		run.TriggerPayload = json.RawMessage("{}")
	}
	if completedAt.Valid {
		run.CompletedAt = &completedAt.Time
	}
	if errMsg.Valid {
		run.Error = &errMsg.String
	}

	return run, nil
}

func (r *WorkflowRunRepository) FindByCaseID(caseID string, limit, offset int) ([]WorkflowRun, int, error) {
	countQuery := `SELECT COUNT(*)::int FROM workflow_runs WHERE case_id = $1`
	var total int
	if err := database.DB.QueryRow(countQuery, caseID).Scan(&total); err != nil {
		return nil, 0, err
	}

	query := `
		SELECT id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
		FROM workflow_runs
		WHERE case_id = $1
		ORDER BY started_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := database.DB.Query(query, caseID, limit, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	runs := []WorkflowRun{}
	for rows.Next() {
		run := WorkflowRun{}
		var cID sql.NullString
		var peid sql.NullString
		var idk sql.NullString
		var payload sql.NullString
		var completedAt sql.NullTime
		var errMsg sql.NullString

		if err := rows.Scan(
			&run.ID,
			&run.WorkflowID,
			&run.Status,
			&cID,
			&peid,
			&idk,
			&payload,
			&run.StartedAt,
			&completedAt,
			&errMsg,
		); err != nil {
			return nil, 0, err
		}

		if cID.Valid {
			run.CaseID = &cID.String
		}
		if peid.Valid {
			run.ProviderEventID = &peid.String
		}
		if idk.Valid {
			run.IdempotencyKey = &idk.String
		}
		if payload.Valid {
			run.TriggerPayload = json.RawMessage(payload.String)
		} else {
			run.TriggerPayload = json.RawMessage("{}")
		}
		if completedAt.Valid {
			run.CompletedAt = &completedAt.Time
		}
		if errMsg.Valid {
			run.Error = &errMsg.String
		}

		runs = append(runs, run)
	}

	return runs, total, nil
}

func (r *WorkflowRunRepository) Create(workflowID string, caseID *string, providerEventID *string, idempotencyKey *string, triggerPayload any) (*WorkflowRun, error) {
	id := uuid.New().String()
	payloadJSON, _ := json.Marshal(triggerPayload)

	query := `
		INSERT INTO workflow_runs (id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id, workflow_id, status, case_id, provider_event_id, idempotency_key, trigger_payload, started_at, completed_at, error
	`

	run := &WorkflowRun{}
	var cID sql.NullString
	var peid sql.NullString
	var idk sql.NullString
	var payload sql.NullString
	var completedAt sql.NullTime
	var errMsg sql.NullString

	err := database.DB.QueryRow(query, id, workflowID, WorkflowRunStatusRunning, caseID, providerEventID, idempotencyKey, payloadJSON).Scan(
		&run.ID, &run.WorkflowID, &run.Status, &cID, &peid, &idk, &payload, &run.StartedAt, &completedAt, &errMsg,
	)
	if err != nil {
		return nil, err
	}

	if cID.Valid {
		run.CaseID = &cID.String
	}
	if peid.Valid {
		run.ProviderEventID = &peid.String
	}
	if idk.Valid {
		run.IdempotencyKey = &idk.String
	}
	if payload.Valid {
		run.TriggerPayload = json.RawMessage(payload.String)
	} else {
		run.TriggerPayload = json.RawMessage("{}")
	}

	return run, nil
}

func (r *WorkflowRunRepository) MarkCompleted(id string) error {
	_, err := database.DB.Exec(`UPDATE workflow_runs SET status = $1, completed_at = NOW() WHERE id = $2`, WorkflowRunStatusCompleted, id)
	return err
}

func (r *WorkflowRunRepository) MarkFailed(id string, errMsg string) error {
	_, err := database.DB.Exec(`UPDATE workflow_runs SET status = $1, error = $2, completed_at = NOW() WHERE id = $3`, WorkflowRunStatusFailed, errMsg, id)
	return err
}
