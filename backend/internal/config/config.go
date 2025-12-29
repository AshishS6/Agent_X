package config

import (
	"os"
	"strconv"
	"strings"

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
