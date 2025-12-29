.PHONY: build run dev test clean deps

# Build the application
build:
	go build -o bin/server ./cmd/server

# Run the application
run: build
	./bin/server

# Run in development mode with hot reload (requires air)
dev:
	@if command -v air > /dev/null; then \
		air; \
	else \
		echo "Air not installed. Running without hot reload..."; \
		go run ./cmd/server; \
	fi

# Run tests
test:
	go test -v ./...

# Clean build artifacts
clean:
	rm -rf bin/
	go clean

# Install dependencies
deps:
	go mod download
	go mod tidy

# Install dev tools
dev-tools:
	go install github.com/cosmtrek/air@latest

# Format code
fmt:
	go fmt ./...

# Lint code
lint:
	golangci-lint run

# Database migration (placeholder)
migrate:
	@echo "Database uses same schema as Node.js backend"
	@echo "See ../database/schema.sql"
