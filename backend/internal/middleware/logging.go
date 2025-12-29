package middleware

import (
	"log"
	"time"

	"github.com/gin-gonic/gin"
)

// LoggingMiddleware logs HTTP requests
func LoggingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		startTime := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		// Process request
		c.Next()

		// Calculate latency
		latency := time.Since(startTime)

		// Log format
		log.Printf("[%s] %s %s %d %v",
			c.Request.Method,
			path,
			query,
			c.Writer.Status(),
			latency,
		)
	}
}
