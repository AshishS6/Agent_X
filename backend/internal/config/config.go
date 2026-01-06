package config

import (
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	Port                        string
	GinMode                     string
	DatabaseURL                 string
	GlobalConcurrencyLimit      int
	DefaultToolConcurrencyLimit int
	CORSOrigins                 []string
	LogLevel                    string
	LLMProvider                 string
	OpenAIAPIKey                string
	MarketResearchTimeout       time.Duration
	SalesAgentTimeout           time.Duration
}

var AppConfig *Config

func Load() *Config {
	// Load .env file if it exists
	godotenv.Load()

	config := &Config{
		Port:                        getEnv("PORT", "3001"),
		GinMode:                     getEnv("GIN_MODE", "debug"),
		DatabaseURL:                 getEnv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/agent_x?sslmode=disable"),
		GlobalConcurrencyLimit:      getEnvInt("GLOBAL_CONCURRENCY_LIMIT", 10),
		DefaultToolConcurrencyLimit: getEnvInt("DEFAULT_TOOL_CONCURRENCY_LIMIT", 5),
		CORSOrigins:                 strings.Split(getEnv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"), ","),
		LogLevel:                    getEnv("LOG_LEVEL", "info"),
		LLMProvider:                 getEnv("LLM_PROVIDER", "openai"),
		OpenAIAPIKey:                getEnv("OPENAI_API_KEY", ""),
		MarketResearchTimeout:       getEnvDuration("MARKET_RESEARCH_TIMEOUT", 10*time.Minute),
		SalesAgentTimeout:           getEnvDuration("SALES_AGENT_TIMEOUT", 3*time.Minute),
	}

	AppConfig = config
	return config
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
		// Try parsing as minutes (e.g., "10" = 10 minutes)
		if minutes, err := strconv.Atoi(value); err == nil {
			return time.Duration(minutes) * time.Minute
		}
	}
	return defaultValue
}
