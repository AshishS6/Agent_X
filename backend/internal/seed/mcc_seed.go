package seed

import (
	"database/sql"
	"encoding/json"
	"io"
	"log"
	"os"
)

// MCC represents the structure of an MCC entry in the JSON file
type MCC struct {
	Code        string   `json:"mcc"`
	Description string   `json:"description"`
	Category    string   `json:"category"`
	Subcategory string   `json:"subcategory"`
	Range       string   `json:"range"`
	Networks    []string `json:"networks"`
	Version     string   `json:"version"`
	Active      bool     `json:"active"`
}

// SeedMccCodes populates the mcc_codes table from the JSON master file
func SeedMccCodes(db *sql.DB, jsonPath string) error {
	// Check if seeding is needed (simple check: is table empty?)
	// Or we can just use ON CONFLICT to upsert/ignore

	log.Printf("🌱 Seeding MCC codes from %s...", jsonPath)

	file, err := os.Open(jsonPath)
	if err != nil {
		return err
	}
	defer file.Close()

	bytes, err := io.ReadAll(file)
	if err != nil {
		return err
	}

	var mccs []MCC
	if err := json.Unmarshal(bytes, &mccs); err != nil {
		return err
	}

	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	insertedCount := 0
	// Prepare statement for efficiency
	// go-lib/pq requires specific handling for arrays, often cleaner to just format the string for simple arrays or use pq.Array
	// Since we don't want to add external dependencies here if possible, we'll format the array manually or assume string[] support
	// Standard SQL driver might need pq.Array for TEXT[]
	// Assuming standard postgres driver is used which usually supports string array literals like '{V,M}'

	stmt, err := tx.Prepare(`
		INSERT INTO mcc_codes (mcc, description, category, subcategory, range, networks, version, active)
		VALUES ($1, $2, $3, $4, $5, $6, $7::date, $8)
		ON CONFLICT (mcc) DO NOTHING
	`)
	if err != nil {
		log.Printf("Error preparing statement: %v", err)
		return err // Fail fast if SQL syntax is wrong
	}
	defer stmt.Close()

	for _, mcc := range mccs {
		// Convert networks slice to PostgreSQL array literal format "{A,B}"
		// or rely on driver. For generic usage, literal string is safest if driver doesn't auto-convert
		// Let's construct the literal manually to be safe without `lib/pq` import visible here
		networksStr := "{"
		for i, n := range mcc.Networks {
			if i > 0 {
				networksStr += ","
			}
			networksStr += n
		}
		networksStr += "}"

		res, err := stmt.Exec(
			mcc.Code,
			mcc.Description,
			mcc.Category,
			mcc.Subcategory,
			mcc.Range,
			networksStr,
			mcc.Version,
			mcc.Active,
		)
		if err != nil {
			log.Printf("Error inserting MCC %s: %v", mcc.Code, err)
			continue
		}

		rows, _ := res.RowsAffected()
		if rows > 0 {
			insertedCount++
		}
	}

	if err := tx.Commit(); err != nil {
		return err
	}

	log.Printf("✅ Seeding complete. Inserted %d new MCC codes.", insertedCount)
	return nil
}
