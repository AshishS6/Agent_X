package models

import (
	"database/sql"
	"log"
	"strings"
	"time"

	"go-backend/internal/database"
)

// MCC represents a merchant category code
type Mcc struct {
	Code        string    `json:"code"`
	Description string    `json:"description"`
	Category    string    `json:"category"`
	Subcategory string    `json:"subcategory"`
	Range       string    `json:"range"`
	Networks    []string  `json:"networks"` // simplified as string array in struct, handling varies by DB driver
	RiskLevel   string    `json:"risk_level"`
	Active      bool      `json:"active"`
	Version     time.Time `json:"version"`
}

// MccAuditLog represents the audit trail for a final MCC decision
type MccAuditLog struct {
	ID         int       `json:"id"`
	ScanID     string    `json:"scan_id"`
	Mcc        string    `json:"mcc"`
	SelectedBy string    `json:"selected_by"` // user_id or "system"
	Source     string    `json:"source"`      // "manual", "auto", "override"
	Reason     string    `json:"reason"`
	Timestamp  time.Time `json:"timestamp"`
}

type MccRepository struct{}

func NewMccRepository() *MccRepository {
	return &MccRepository{}
}

// InitMccTables creates the necessary tables if they don't exist
func InitMccTables() error {
	log.Println("🛠️ Initializing MCC tables...")

	// 1. MCC Codes Master Table
	// Using TEXT[] for networks if using Postgres. For generic SQL, might need normalization or JSON string.
	// Assuming Postgres based on "TEXT[]" request.
	mccTable := `
	CREATE TABLE IF NOT EXISTS mcc_codes (
		mcc VARCHAR(4) PRIMARY KEY,
		description TEXT NOT NULL,
		category TEXT NOT NULL,
		subcategory TEXT NOT NULL,
		range TEXT NOT NULL,
		networks TEXT[] NOT NULL,
		risk_level TEXT DEFAULT 'medium',
		active BOOLEAN DEFAULT TRUE,
		version DATE NOT NULL
	);`

	if _, err := database.DB.Exec(mccTable); err != nil {
		return err
	}

	// 2. MCC Audit Logs
	auditTable := `
	CREATE TABLE IF NOT EXISTS mcc_audit_logs (
		id SERIAL PRIMARY KEY,
		scan_id VARCHAR(255) NOT NULL,
		mcc VARCHAR(4) NOT NULL,
		selected_by VARCHAR(255) NOT NULL,
		source VARCHAR(50) NOT NULL,
		reason TEXT,
		timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mcc) REFERENCES mcc_codes(mcc)
	);`

	if _, err := database.DB.Exec(auditTable); err != nil {
		return err
	}

	return nil
}

// GetAll returns all active MCCs (or all if activeOnly is false)
func (r *MccRepository) GetAll(activeOnly bool) ([]Mcc, error) {
	query := `
		SELECT mcc, description, category, subcategory, range, networks, risk_level, active, version 
		FROM mcc_codes 
		WHERE 1=1
	`
	if activeOnly {
		query += ` AND active = TRUE`
	}
	query += ` ORDER BY mcc ASC`

	rows, err := database.DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var mccs []Mcc
	for rows.Next() {
		var m Mcc
		var netStr string

		if err := rows.Scan(
			&m.Code, &m.Description, &m.Category, &m.Subcategory, &m.Range,
			&netStr,
			&m.RiskLevel, &m.Active, &m.Version,
		); err != nil {
			return nil, err
		}

		// Parse "{a,b}" to []string
		if len(netStr) > 2 {
			content := netStr[1 : len(netStr)-1] // remove {}
			m.Networks = strings.Split(content, ",")
		}

		mccs = append(mccs, m)
	}
	return mccs, nil
}

// GetByCode retrieves a single MCC
func (r *MccRepository) GetByCode(code string) (*Mcc, error) {
	query := `
		SELECT mcc, description, category, subcategory, range, networks, risk_level, active, version 
		FROM mcc_codes 
		WHERE mcc = $1
	`
	var m Mcc
	var netStr string
	err := database.DB.QueryRow(query, code).Scan(
		&m.Code, &m.Description, &m.Category, &m.Subcategory, &m.Range,
		&netStr,
		&m.RiskLevel, &m.Active, &m.Version,
	)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	if len(netStr) > 2 {
		content := netStr[1 : len(netStr)-1] // remove {}
		m.Networks = strings.Split(content, ",")
	}
	return &m, nil
}

// CreateAuditLog inserts a new audit log
func (r *MccRepository) CreateAuditLog(logEntry MccAuditLog) error {
	query := `
		INSERT INTO mcc_audit_logs (scan_id, mcc, selected_by, source, reason, timestamp)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	_, err := database.DB.Exec(query,
		logEntry.ScanID, logEntry.Mcc, logEntry.SelectedBy, logEntry.Source, logEntry.Reason, time.Now(),
	)
	return err
}
