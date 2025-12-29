package middleware

import (
	"strings"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// CORSMiddleware returns a CORS middleware configured with the given origins
func CORSMiddleware(origins []string) gin.HandlerFunc {
	config := cors.Config{
		AllowOrigins:     origins,
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}

	// If wildcard is specified, allow all origins
	for _, origin := range origins {
		if strings.TrimSpace(origin) == "*" {
			config.AllowAllOrigins = true
			config.AllowOrigins = nil
			break
		}
	}

	return cors.New(config)
}
