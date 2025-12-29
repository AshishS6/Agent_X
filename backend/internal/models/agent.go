package models

import (
	"database/sql"
	"encoding/json"
	"time"

	"go-backend/internal/database"
)

type AgentStatus string

const (
	AgentStatusActive AgentStatus = "active"
	AgentStatusPaused AgentStatus = "paused"
	AgentStatusError  AgentStatus = "error"
)

type Agent struct {
	ID          string          `json:"id"`
	Type        string          `json:"type"`
	Name        string          `json:"name"`
	Description string          `json:"description"`
	Status      AgentStatus     `json:"status"`
	Config      json.RawMessage `json:"config"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

type AgentRepository struct{}

func NewAgentRepository() *AgentRepository {
	return &AgentRepository{}
}

func (r *AgentRepository) FindAll() ([]Agent, error) {
	query := `SELECT id, type, name, description, status, config, created_at, updated_at FROM agents ORDER BY created_at DESC`

	rows, err := database.DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	agents := []Agent{}
	for rows.Next() {
		agent := Agent{}
		var config sql.NullString

		err := rows.Scan(
			&agent.ID, &agent.Type, &agent.Name, &agent.Description,
			&agent.Status, &config, &agent.CreatedAt, &agent.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}

		if config.Valid {
			agent.Config = json.RawMessage(config.String)
		} else {
			agent.Config = json.RawMessage("{}")
		}

		agents = append(agents, agent)
	}

	return agents, nil
}

func (r *AgentRepository) FindByID(id string) (*Agent, error) {
	query := `SELECT id, type, name, description, status, config, created_at, updated_at FROM agents WHERE id = $1`

	agent := &Agent{}
	var config sql.NullString

	err := database.DB.QueryRow(query, id).Scan(
		&agent.ID, &agent.Type, &agent.Name, &agent.Description,
		&agent.Status, &config, &agent.CreatedAt, &agent.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if config.Valid {
		agent.Config = json.RawMessage(config.String)
	} else {
		agent.Config = json.RawMessage("{}")
	}

	return agent, nil
}

func (r *AgentRepository) FindByType(agentType string) (*Agent, error) {
	query := `SELECT id, type, name, description, status, config, created_at, updated_at FROM agents WHERE type = $1`

	agent := &Agent{}
	var config sql.NullString

	err := database.DB.QueryRow(query, agentType).Scan(
		&agent.ID, &agent.Type, &agent.Name, &agent.Description,
		&agent.Status, &config, &agent.CreatedAt, &agent.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if config.Valid {
		agent.Config = json.RawMessage(config.String)
	} else {
		agent.Config = json.RawMessage("{}")
	}

	return agent, nil
}

func (r *AgentRepository) Update(id string, updates map[string]any) (*Agent, error) {
	// Build dynamic update query
	setClauses := []string{}
	args := []any{}
	argNum := 1

	if name, ok := updates["name"].(string); ok {
		setClauses = append(setClauses, "name = $"+string(rune('0'+argNum)))
		args = append(args, name)
		argNum++
	}
	if description, ok := updates["description"].(string); ok {
		setClauses = append(setClauses, "description = $"+string(rune('0'+argNum)))
		args = append(args, description)
		argNum++
	}
	if status, ok := updates["status"].(string); ok {
		setClauses = append(setClauses, "status = $"+string(rune('0'+argNum)))
		args = append(args, status)
		argNum++
	}
	if config, ok := updates["config"]; ok {
		configJSON, _ := json.Marshal(config)
		setClauses = append(setClauses, "config = $"+string(rune('0'+argNum)))
		args = append(args, configJSON)
		argNum++
	}

	if len(setClauses) == 0 {
		return r.FindByID(id)
	}

	// Always update updated_at
	setClauses = append(setClauses, "updated_at = NOW()")
	args = append(args, id)

	query := "UPDATE agents SET "
	for i, clause := range setClauses {
		if i > 0 {
			query += ", "
		}
		query += clause
	}
	query += " WHERE id = $" + string(rune('0'+argNum)) + " RETURNING id, type, name, description, status, config, created_at, updated_at"

	agent := &Agent{}
	var config sql.NullString

	err := database.DB.QueryRow(query, args...).Scan(
		&agent.ID, &agent.Type, &agent.Name, &agent.Description,
		&agent.Status, &config, &agent.CreatedAt, &agent.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}

	if config.Valid {
		agent.Config = json.RawMessage(config.String)
	} else {
		agent.Config = json.RawMessage("{}")
	}

	return agent, nil
}
