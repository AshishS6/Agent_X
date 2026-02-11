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

type IntegrationStatus string

const (
	IntegrationStatusConnected    IntegrationStatus = "connected"
	IntegrationStatusError        IntegrationStatus = "error"
	IntegrationStatusDisconnected IntegrationStatus = "disconnected"
)

type Integration struct {
	ID        string            `json:"id"`
	Name      string            `json:"name"`
	Type      string            `json:"type"`
	Status    IntegrationStatus `json:"status"`
	Config    json.RawMessage   `json:"config"`
	LastSync  *time.Time        `json:"last_sync,omitempty"`
	CreatedAt time.Time         `json:"created_at"`
}

type IntegrationRepository struct{}

func NewIntegrationRepository() *IntegrationRepository {
	return &IntegrationRepository{}
}

func (r *IntegrationRepository) FindAll() ([]Integration, error) {
	query := `SELECT id, name, type, status, config, last_sync, created_at FROM integrations ORDER BY created_at DESC`

	rows, err := database.DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := []Integration{}
	for rows.Next() {
		it := Integration{}
		var config sql.NullString
		var lastSync sql.NullTime

		if err := rows.Scan(&it.ID, &it.Name, &it.Type, &it.Status, &config, &lastSync, &it.CreatedAt); err != nil {
			return nil, err
		}

		if config.Valid {
			it.Config = json.RawMessage(config.String)
		} else {
			it.Config = json.RawMessage("{}")
		}
		if lastSync.Valid {
			it.LastSync = &lastSync.Time
		}

		result = append(result, it)
	}

	return result, nil
}

func (r *IntegrationRepository) FindByID(id string) (*Integration, error) {
	query := `SELECT id, name, type, status, config, last_sync, created_at FROM integrations WHERE id = $1`

	it := &Integration{}
	var config sql.NullString
	var lastSync sql.NullTime

	err := database.DB.QueryRow(query, id).Scan(&it.ID, &it.Name, &it.Type, &it.Status, &config, &lastSync, &it.CreatedAt)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if config.Valid {
		it.Config = json.RawMessage(config.String)
	} else {
		it.Config = json.RawMessage("{}")
	}
	if lastSync.Valid {
		it.LastSync = &lastSync.Time
	}

	return it, nil
}

func (r *IntegrationRepository) Create(name, integrationType string, status IntegrationStatus, config any) (*Integration, error) {
	id := uuid.New().String()
	configJSON, _ := json.Marshal(config)

	query := `
		INSERT INTO integrations (id, name, type, status, config)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING id, name, type, status, config, last_sync, created_at
	`

	it := &Integration{}
	var configStr sql.NullString
	var lastSync sql.NullTime

	err := database.DB.QueryRow(query, id, name, integrationType, status, configJSON).Scan(
		&it.ID, &it.Name, &it.Type, &it.Status, &configStr, &lastSync, &it.CreatedAt,
	)
	if err != nil {
		return nil, err
	}

	if configStr.Valid {
		it.Config = json.RawMessage(configStr.String)
	} else {
		it.Config = json.RawMessage("{}")
	}
	if lastSync.Valid {
		it.LastSync = &lastSync.Time
	}

	return it, nil
}

func (r *IntegrationRepository) Update(id string, updates map[string]any) (*Integration, error) {
	setClauses := []string{}
	args := []any{}
	argCount := 1

	if name, ok := updates["name"].(string); ok {
		setClauses = append(setClauses, "name = $"+strconv.Itoa(argCount))
		args = append(args, name)
		argCount++
	}
	if t, ok := updates["type"].(string); ok {
		setClauses = append(setClauses, "type = $"+strconv.Itoa(argCount))
		args = append(args, t)
		argCount++
	}
	if status, ok := updates["status"].(string); ok {
		setClauses = append(setClauses, "status = $"+strconv.Itoa(argCount))
		args = append(args, status)
		argCount++
	}
	if cfg, ok := updates["config"]; ok {
		cfgJSON, _ := json.Marshal(cfg)
		setClauses = append(setClauses, "config = $"+strconv.Itoa(argCount))
		args = append(args, cfgJSON)
		argCount++
	}

	// Accept both snake_case and camelCase from frontend
	lastSyncRaw, hasLastSync := updates["last_sync"]
	if !hasLastSync {
		lastSyncRaw, hasLastSync = updates["lastSync"]
	}

	if hasLastSync {
		// Accept RFC3339 string, time.Time, or nil
		if lastSyncRaw == nil {
			setClauses = append(setClauses, "last_sync = NULL")
		} else {
			switch v := lastSyncRaw.(type) {
			case string:
				parsed, err := time.Parse(time.RFC3339, v)
				if err == nil {
					setClauses = append(setClauses, "last_sync = $"+strconv.Itoa(argCount))
					args = append(args, parsed)
					argCount++
				}
			case time.Time:
				setClauses = append(setClauses, "last_sync = $"+strconv.Itoa(argCount))
				args = append(args, v)
				argCount++
			}
		}
	}

	if len(setClauses) == 0 {
		return r.FindByID(id)
	}

	args = append(args, id)

	query := "UPDATE integrations SET " + strings.Join(setClauses, ", ") + " WHERE id = $" + strconv.Itoa(argCount) +
		" RETURNING id, name, type, status, config, last_sync, created_at"

	it := &Integration{}
	var configStr sql.NullString
	var lastSync sql.NullTime

	err := database.DB.QueryRow(query, args...).Scan(&it.ID, &it.Name, &it.Type, &it.Status, &configStr, &lastSync, &it.CreatedAt)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if configStr.Valid {
		it.Config = json.RawMessage(configStr.String)
	} else {
		it.Config = json.RawMessage("{}")
	}
	if lastSync.Valid {
		it.LastSync = &lastSync.Time
	}

	return it, nil
}

func (r *IntegrationRepository) Delete(id string) error {
	_, err := database.DB.Exec(`DELETE FROM integrations WHERE id = $1`, id)
	return err
}
