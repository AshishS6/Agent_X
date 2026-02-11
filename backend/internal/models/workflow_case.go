package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"go-backend/internal/database"

	"github.com/google/uuid"
)

type WorkflowCase struct {
	ID            string          `json:"id"`
	WorkflowID    string          `json:"workflow_id"`
	Provider      string          `json:"provider"`
	ExternalRefID string          `json:"external_ref_id"`
	Status        *string         `json:"status,omitempty"`
	LatestState   json.RawMessage `json:"latest_state"`
	CreatedAt     time.Time       `json:"created_at"`
	UpdatedAt     time.Time       `json:"updated_at"`
}

type WorkflowCaseRepository struct{}

func NewWorkflowCaseRepository() *WorkflowCaseRepository {
	return &WorkflowCaseRepository{}
}

func (r *WorkflowCaseRepository) FindByID(id string) (*WorkflowCase, error) {
	query := `
		SELECT id, workflow_id, provider, external_ref_id, status, latest_state, created_at, updated_at
		FROM workflow_cases
		WHERE id = $1
	`

	c := &WorkflowCase{}
	var status sql.NullString
	var latest sql.NullString

	err := database.DB.QueryRow(query, id).Scan(
		&c.ID, &c.WorkflowID, &c.Provider, &c.ExternalRefID, &status, &latest, &c.CreatedAt, &c.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if status.Valid {
		c.Status = &status.String
	}
	if latest.Valid {
		c.LatestState = json.RawMessage(latest.String)
	} else {
		c.LatestState = json.RawMessage("{}")
	}
	return c, nil
}

func (r *WorkflowCaseRepository) FindOrCreateByExternalRef(workflowID, provider, externalRefID string) (*WorkflowCase, error) {
	// Try find first
	found, err := r.FindByExternalRef(workflowID, provider, externalRefID)
	if err != nil {
		return nil, err
	}
	if found != nil {
		return found, nil
	}

	id := uuid.New().String()
	query := `
		INSERT INTO workflow_cases (id, workflow_id, provider, external_ref_id, latest_state)
		VALUES ($1, $2, $3, $4, '{}'::jsonb)
		ON CONFLICT (workflow_id, provider, external_ref_id) DO UPDATE SET updated_at = NOW()
		RETURNING id, workflow_id, provider, external_ref_id, status, latest_state, created_at, updated_at
	`

	c := &WorkflowCase{}
	var status sql.NullString
	var latest sql.NullString

	err = database.DB.QueryRow(query, id, workflowID, provider, externalRefID).Scan(
		&c.ID, &c.WorkflowID, &c.Provider, &c.ExternalRefID, &status, &latest, &c.CreatedAt, &c.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	if status.Valid {
		c.Status = &status.String
	}
	if latest.Valid {
		c.LatestState = json.RawMessage(latest.String)
	} else {
		c.LatestState = json.RawMessage("{}")
	}
	return c, nil
}

func (r *WorkflowCaseRepository) FindByExternalRef(workflowID, provider, externalRefID string) (*WorkflowCase, error) {
	query := `
		SELECT id, workflow_id, provider, external_ref_id, status, latest_state, created_at, updated_at
		FROM workflow_cases
		WHERE workflow_id = $1 AND provider = $2 AND external_ref_id = $3
		LIMIT 1
	`

	c := &WorkflowCase{}
	var status sql.NullString
	var latest sql.NullString

	err := database.DB.QueryRow(query, workflowID, provider, externalRefID).Scan(
		&c.ID, &c.WorkflowID, &c.Provider, &c.ExternalRefID, &status, &latest, &c.CreatedAt, &c.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if status.Valid {
		c.Status = &status.String
	}
	if latest.Valid {
		c.LatestState = json.RawMessage(latest.String)
	} else {
		c.LatestState = json.RawMessage("{}")
	}
	return c, nil
}

func (r *WorkflowCaseRepository) ListByWorkflowID(workflowID string, limit, offset int) ([]WorkflowCase, int, error) {
	countQuery := `SELECT COUNT(*)::int FROM workflow_cases WHERE workflow_id = $1`
	var total int
	if err := database.DB.QueryRow(countQuery, workflowID).Scan(&total); err != nil {
		return nil, 0, err
	}

	query := `
		SELECT id, workflow_id, provider, external_ref_id, status, latest_state, created_at, updated_at
		FROM workflow_cases
		WHERE workflow_id = $1
		ORDER BY updated_at DESC
		LIMIT $2 OFFSET $3
	`

	rows, err := database.DB.Query(query, workflowID, limit, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	out := []WorkflowCase{}
	for rows.Next() {
		c := WorkflowCase{}
		var status sql.NullString
		var latest sql.NullString
		if err := rows.Scan(&c.ID, &c.WorkflowID, &c.Provider, &c.ExternalRefID, &status, &latest, &c.CreatedAt, &c.UpdatedAt); err != nil {
			return nil, 0, err
		}
		if status.Valid {
			c.Status = &status.String
		}
		if latest.Valid {
			c.LatestState = json.RawMessage(latest.String)
		} else {
			c.LatestState = json.RawMessage("{}")
		}
		out = append(out, c)
	}

	return out, total, nil
}

func (r *WorkflowCaseRepository) UpdateLatestState(id string, latestState any) error {
	stateJSON, _ := json.Marshal(latestState)
	_, err := database.DB.Exec(`UPDATE workflow_cases SET latest_state = $1 WHERE id = $2`, stateJSON, id)
	return err
}
