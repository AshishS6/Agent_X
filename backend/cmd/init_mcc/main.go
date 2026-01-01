package main

import (
	"log"
	"os"
	"path/filepath"

	"go-backend/internal/config"
	"go-backend/internal/database"
	"go-backend/internal/models"
	"go-backend/internal/seed"
)

func main() {
	log.Println("🔧 Manual MCC Initialization Script")

	// Load configuration
	cfg := config.Load()

	// Connect to database
	if err := database.Connect(cfg.DatabaseURL); err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}
	defer database.Close()
	log.Println("✅ Database connected")

	// Get project root
	cwd, _ := os.Getwd()
	// Assuming running from backend dir
	projectRoot := filepath.Dir(cwd)

	// Quick fix for path if running from root vs backend
	if filepath.Base(cwd) == "Agent_X" {
		projectRoot = cwd
	}

	log.Printf("📁 Project root: %s", projectRoot)

	// Initialize Tables
	if err := models.InitMccTables(); err != nil {
		log.Fatalf("❌ Failed to initialize MCC tables: %v", err)
	}
	log.Println("✅ MCC Tables Initialized")

	// Run Seeder
	jsonPath := filepath.Join(projectRoot, "database", "mcc_master.json")
	log.Printf("📄 Seeding from: %s", jsonPath)

	if err := seed.SeedMccCodes(database.DB, jsonPath); err != nil {
		log.Fatalf("❌ Failed to seed: %v", err)
	}
	log.Println("✅ Seeding Complete")
}
