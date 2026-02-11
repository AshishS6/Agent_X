package models

import (
	"database/sql"
	"encoding/json"
	"strconv"
	"strings"
	"time"

	"go-backend/internal/database"

	"github.com/google/uuid"
)

type WorkflowStatus string

const (
	WorkflowStatusActive WorkflowStatus = "active"
	WorkflowStatusPaused WorkflowStatus = "paused"
	WorkflowStatusDraft  WorkflowStatus = "draft"
)

type Workflow struct {
	ID            string          `json:"id"`
	Name          string          `json:"name"`
	Description   *string         `json:"description,omitempty"`
	Status        WorkflowStatus  `json:"status"`
	TriggerType   string          `json:"trigger_type"`
	TriggerConfig json.RawMessage `json:"trigger_config"`
	Steps         json.RawMessage `json:"steps"`
	OwnerTeam     *string         `json:"owner_team,omitempty"`
	CreatedBy     *string         `json:"created_by,omitempty"`
	CreatedAt     time.Time       `json:"created_at"`
	UpdatedAt     time.Time       `json:"updated_at"`
}

type WorkflowRepository struct{}

func NewWorkflowRepository() *WorkflowRepository {
	return &WorkflowRepository{}
}

func (r *WorkflowRepository) FindAll() ([]Workflow, error) {
	query := `
		SELECT id, name, description, status, trigger_type, trigger_config, steps, owner_team, created_by, created_at, updated_at
		FROM workflows
		ORDER BY created_at DESC
	`

	rows, err := database.DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := []Workflow{}
	for rows.Next() {
		w := Workflow{}
		var description sql.NullString
		var triggerConfig sql.NullString
		var steps sql.NullString
		var ownerTeam sql.NullString
		var createdBy sql.NullString

		if err := rows.Scan(
			&w.ID,
			&w.Name,
			&description,
			&w.Status,
			&w.TriggerType,
			&triggerConfig,
			&steps,
			&ownerTeam,
			&createdBy,
			&w.CreatedAt,
			&w.UpdatedAt,
		); err != nil {
			return nil, err
		}

		if description.Valid {
			w.Description = &description.String
		}
		if triggerConfig.Valid {
			w.TriggerConfig = json.RawMessage(triggerConfig.String)
		} else {
			w.TriggerConfig = json.RawMessage("{}")
		}
		if steps.Valid {
			w.Steps = json.RawMessage(steps.String)
		} else {
			w.Steps = json.RawMessage("[]")
		}
		if ownerTeam.Valid {
			w.OwnerTeam = &ownerTeam.String
		}
		if createdBy.Valid {
			w.CreatedBy = &createdBy.String
		}

		result = append(result, w)
	}

	return result, nil
}

func (r *WorkflowRepository) FindByID(id string) (*Workflow, error) {
	query := `
		SELECT id, name, description, status, trigger_type, trigger_config, steps, owner_team, created_by, created_at, updated_at
		FROM workflows
		WHERE id = $1
	`

	w := &Workflow{}
	var description sql.NullString
	var triggerConfig sql.NullString
	var steps sql.NullString
	var ownerTeam sql.NullString
	var createdBy sql.NullString

	err := database.DB.QueryRow(query, id).Scan(
		&w.ID,
		&w.Name,
		&description,
		&w.Status,
		&w.TriggerType,
		&triggerConfig,
		&steps,
		&ownerTeam,
		&createdBy,
		&w.CreatedAt,
		&w.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if description.Valid {
		w.Description = &description.String
	}
	if triggerConfig.Valid {
		w.TriggerConfig = json.RawMessage(triggerConfig.String)
	} else {
		w.TriggerConfig = json.RawMessage("{}")
	}
	if steps.Valid {
		w.Steps = json.RawMessage(steps.String)
	} else {
		w.Steps = json.RawMessage("[]")
	}
	if ownerTeam.Valid {
		w.OwnerTeam = &ownerTeam.String
	}
	if createdBy.Valid {
		w.CreatedBy = &createdBy.String
	}

	return w, nil
}

func (r *WorkflowRepository) Create(
	name string,
	description string,
	status WorkflowStatus,
	triggerType string,
	triggerConfig any,
	steps any,
	ownerTeam string,
	createdBy string,
) (*Workflow, error) {
	id := uuid.New().String()

	var descPtr *string
	if description != "" {
		descPtr = &description
	}
	var ownerPtr *string
	if ownerTeam != "" {
		ownerPtr = &ownerTeam
	}
	var createdByPtr *string
	if createdBy != "" {
		createdByPtr = &createdBy
	}

	triggerConfigJSON, _ := json.Marshal(triggerConfig)
	stepsJSON, _ := json.Marshal(steps)

	query := `
		INSERT INTO workflows (id, name, description, status, trigger_type, trigger_config, steps, owner_team, created_by)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		RETURNING id, name, description, status, trigger_type, trigger_config, steps, owner_team, created_by, created_at, updated_at
	`

	w := &Workflow{}
	var desc sql.NullString
	var trigCfg sql.NullString
	var stepsStr sql.NullString
	var owner sql.NullString
	var creator sql.NullString

	err := database.DB.QueryRow(
		query,
		id,
		name,
		descPtr,
		status,
		triggerType,
		triggerConfigJSON,
		stepsJSON,
		ownerPtr,
		createdByPtr,
	).Scan(
		&w.ID, &w.Name, &desc, &w.Status, &w.TriggerType, &trigCfg, &stepsStr, &owner, &creator, &w.CreatedAt, &w.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}

	if desc.Valid {
		w.Description = &desc.String
	}
	if trigCfg.Valid {
		w.TriggerConfig = json.RawMessage(trigCfg.String)
	} else {
		w.TriggerConfig = json.RawMessage("{}")
	}
	if stepsStr.Valid {
		w.Steps = json.RawMessage(stepsStr.String)
	} else {
		w.Steps = json.RawMessage("[]")
	}
	if owner.Valid {
		w.OwnerTeam = &owner.String
	}
	if creator.Valid {
		w.CreatedBy = &creator.String
	}

	return w, nil
}

func (r *WorkflowRepository) Update(id string, updates map[string]any) (*Workflow, error) {
	setClauses := []string{}
	args := []any{}
	argCount := 1

	if name, ok := updates["name"].(string); ok {
		setClauses = append(setClauses, "name = $"+strconv.Itoa(argCount))
		args = append(args, name)
		argCount++
	}
	if description, ok := updates["description"]; ok {
		if description == nil {
			setClauses = append(setClauses, "description = NULL")
		} else if descStr, ok := description.(string); ok {
			setClauses = append(setClauses, "description = $"+strconv.Itoa(argCount))
			args = append(args, descStr)
			argCount++
		}
	}
	if status, ok := updates["status"].(string); ok {
		setClauses = append(setClauses, "status = $"+strconv.Itoa(argCount))
		args = append(args, status)
		argCount++
	}
	if triggerType, ok := updates["trigger_type"].(string); ok {
		setClauses = append(setClauses, "trigger_type = $"+strconv.Itoa(argCount))
		args = append(args, triggerType)
		argCount++
	}
	if triggerConfig, ok := updates["trigger_config"]; ok {
		cfgJSON, _ := json.Marshal(triggerConfig)
		setClauses = append(setClauses, "trigger_config = $"+strconv.Itoa(argCount))
		args = append(args, cfgJSON)
		argCount++
	}
	if steps, ok := updates["steps"]; ok {
		stepsJSON, _ := json.Marshal(steps)
		setClauses = append(setClauses, "steps = $"+strconv.Itoa(argCount))
		args = append(args, stepsJSON)
		argCount++
	}
	if ownerTeam, ok := updates["owner_team"]; ok {
		if ownerTeam == nil {
			setClauses = append(setClauses, "owner_team = NULL")
		} else if ownerStr, ok := ownerTeam.(string); ok {
			setClauses = append(setClauses, "owner_team = $"+strconv.Itoa(argCount))
			args = append(args, ownerStr)
			argCount++
		}
	}
	if createdBy, ok := updates["created_by"]; ok {
		if createdBy == nil {
			setClauses = append(setClauses, "created_by = NULL")
		} else if creatorStr, ok := createdBy.(string); ok {
			setClauses = append(setClauses, "created_by = $"+strconv.Itoa(argCount))
			args = append(args, creatorStr)
			argCount++
		}
	}

	if len(setClauses) == 0 {
		return r.FindByID(id)
	}

	// updated_at is handled by DB trigger; keep explicit updates minimal.
	args = append(args, id)
	query := "UPDATE workflows SET " + strings.Join(setClauses, ", ") + " WHERE id = $" + strconv.Itoa(argCount) + " RETURNING id"

	var updatedID string
	if err := database.DB.QueryRow(query, args...).Scan(&updatedID); err == sql.ErrNoRows {
		return nil, nil
	} else if err != nil {
		return nil, err
	}

	return r.FindByID(id)
}
