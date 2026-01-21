package main

import (
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"go-backend/internal/config"
	"go-backend/internal/database"
	"go-backend/internal/handlers"
	"go-backend/internal/middleware"
	"go-backend/internal/models"
	"go-backend/internal/seed"
	"go-backend/internal/tools"

	"github.com/gin-gonic/gin"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Set Gin mode
	gin.SetMode(cfg.GinMode)

	// Connect to database
	if err := database.Connect(cfg.DatabaseURL); err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}
	defer database.Close()
	log.Println("✅ Database connected")

	// Get project root (parent of go-backend)
	cwd, _ := os.Getwd()
	projectRoot := filepath.Dir(cwd)
	if filepath.Base(cwd) != "go-backend" && filepath.Base(cwd) != "backend" {
		// If running from project root, use current directory
		projectRoot = cwd
	}
	log.Printf("📁 Project root: %s", projectRoot)

	// Initialize tool registry with configurable timeouts
	tools.InitRegistry(cfg.MarketResearchTimeout, cfg.SalesAgentTimeout, cfg.BlogAgentTimeout)
	log.Printf("🔧 Tool timeouts configured - Market Research: %v, Sales: %v, Blog: %v",
		cfg.MarketResearchTimeout,
		cfg.SalesAgentTimeout,
		cfg.BlogAgentTimeout,
	)

	// Create executor with hybrid concurrency control
	executor := tools.NewExecutor(
		cfg.GlobalConcurrencyLimit,
		cfg.DefaultToolConcurrencyLimit,
		projectRoot,
	)
	log.Printf("⚡ Executor initialized (global: %d, per-tool default: %d)",
		cfg.GlobalConcurrencyLimit,
		cfg.DefaultToolConcurrencyLimit,
	)

	// Create Gin router
	router := gin.New()

	// Middleware
	router.Use(gin.Recovery())
	router.Use(middleware.LoggingMiddleware())
	router.Use(middleware.CORSMiddleware(cfg.CORSOrigins))

	// Initialize handlers
	agentsHandler := handlers.NewAgentsHandler(executor)
	tasksHandler := handlers.NewTasksHandler(executor)
	monitoringHandler := handlers.NewMonitoringHandler(executor)
	toolsHandler := handlers.NewToolsHandler()
	mccHandler := handlers.NewMccHandler()

	// Initialize MCC Tables & Seed Data
	if err := models.InitMccTables(); err != nil {
		log.Printf("⚠️ Failed to initialize MCC tables: %v", err)
	} else {
		// Run Seeder
		jsonPath := filepath.Join(projectRoot, "database", "mcc_master.json")
		if err := seed.SeedMccCodes(database.DB, jsonPath); err != nil {
			log.Printf("⚠️ Failed to seed MCC codes (could be harmless if file missing or already seeded): %v", err)
		}
	}

	// Root endpoint
	router.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"name":    "Agent_X Go Backend API",
			"version": "2.0.0",
			"status":  "running",
			"endpoints": gin.H{
				"agents":     "/api/agents",
				"tasks":      "/api/tasks",
				"tools":      "/api/tools",
				"monitoring": "/api/monitoring",
				"health":     "/api/monitoring/health",
				"mccs":       "/api/mccs",
			},
		})
	})

	// API routes
	api := router.Group("/api")
	{
		// Agents routes (uses agent type/name for execute)
		agents := api.Group("/agents")
		{
			agents.GET("", agentsHandler.GetAll)
			agents.GET("/:id", agentsHandler.GetByID)
			agents.POST("/:name/execute", agentsHandler.Execute) // Uses agent type (e.g., "market_research")
			agents.PUT("/:id", agentsHandler.Update)
			agents.GET("/:id/metrics", agentsHandler.GetMetrics)
		}

		// Tasks routes
		tasks := api.Group("/tasks")
		{
			tasks.GET("", tasksHandler.GetAll)
			tasks.GET("/status/counts", tasksHandler.GetStatusCounts)
			tasks.GET("/:id", tasksHandler.GetByID)
			tasks.GET("/:id/report", tasksHandler.DownloadReport)

			// MCC Sub-routes for tasks
			tasks.POST("/:id/mcc", mccHandler.SaveFinalMcc)
		}

		// MCC Routes
		api.GET("/mccs", mccHandler.GetMccs)

		// Tools routes (new endpoint)
		toolsGroup := api.Group("/tools")
		{
			toolsGroup.GET("", toolsHandler.ListTools)
			toolsGroup.GET("/:name", toolsHandler.GetTool)
		}

		// Monitoring routes
		monitoring := api.Group("/monitoring")
		{
			monitoring.GET("/health", monitoringHandler.Health)
			monitoring.GET("/metrics", monitoringHandler.Metrics)
			monitoring.GET("/activity", monitoringHandler.Activity)
			monitoring.GET("/system", monitoringHandler.System)
			monitoring.GET("/proxy", monitoringHandler.Proxy)
		}
	}

	// Graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
		<-sigChan

		log.Println("🛑 Shutting down gracefully...")
		database.Close()
		os.Exit(0)
	}()

	// Start server
	addr := ":" + cfg.Port
	log.Printf("🚀 Server starting on port %s", cfg.Port)
	log.Printf("📡 Environment: %s", cfg.GinMode)
	log.Printf("🌐 CORS enabled for: %v", cfg.CORSOrigins)
	log.Println("")
	log.Println("📍 API Documentation:")
	log.Printf("   - Health: http://localhost:%s/api/monitoring/health", cfg.Port)
	log.Printf("   - Agents: http://localhost:%s/api/agents", cfg.Port)
	log.Printf("   - Tasks:  http://localhost:%s/api/tasks", cfg.Port)
	log.Printf("   - Tools:  http://localhost:%s/api/tools", cfg.Port)
	log.Printf("   - MCCs:   http://localhost:%s/api/mccs", cfg.Port)
	log.Println("")

	if err := router.Run(addr); err != nil {
		log.Fatalf("❌ Failed to start server: %v", err)
	}
}
