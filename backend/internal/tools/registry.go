package tools

import (
	"time"
)

// ToolConfig defines a CLI tool that can be executed
type ToolConfig struct {
	Name             string        `json:"name"`
	Description      string        `json:"description"`
	Command          string        `json:"command"`     // e.g., "python"
	Args             []string      `json:"args"`        // e.g., ["agents/market_research_agent/cli.py"]
	Timeout          time.Duration `json:"timeout"`     // Max execution time
	WorkingDir       string        `json:"working_dir"` // Working directory for the command
	ConcurrencyLimit int           `json:"concurrency"` // Per-tool concurrency limit (0 = use default)
	AgentType        string        `json:"agent_type"`  // Maps to agent type in DB (e.g., "market_research")
}

// Registry holds all available tools
// Tool names are used in API paths: /api/agents/{name}/execute
var Registry = map[string]ToolConfig{}

// InitRegistry initializes the tool registry with configurable timeouts
// This should be called from main.go after loading configuration
func InitRegistry(marketResearchTimeout, salesAgentTimeout, blogAgentTimeout time.Duration) {
	Registry = map[string]ToolConfig{
		"market_research": {
			Name:             "Market Research Agent",
			Description:      "Competitor analysis, trend tracking, and market research",
			Command:          "python3",
			Args:             []string{"backend/agents/market_research_agent/cli.py"},
			Timeout:          marketResearchTimeout,
			WorkingDir:       ".",
			ConcurrencyLimit: 5,
			AgentType:        "market_research",
		},
		"site_scan": {
			Name:             "Site Scan Agent",
			Description:      "Website scanning, compliance checks, and KYC site scans",
			Command:          "python3",
			Args:             []string{"backend/agents/site_scan_agent/cli.py"},
			Timeout:          marketResearchTimeout,
			WorkingDir:       ".",
			ConcurrencyLimit: 5,
			AgentType:        "site_scan",
		},
		"sales": {
			Name:             "Sales Agent",
			Description:      "Lead qualification, email outreach, and meeting scheduling automation",
			Command:          "python3",
			Args:             []string{"backend/agents/sales_agent/cli.py"},
			Timeout:          salesAgentTimeout,
			WorkingDir:       ".",
			ConcurrencyLimit: 5,
			AgentType:        "sales",
		},
		"support_ticket_triage": {
			Name:             "Support Ticket Triage Agent",
			Description:      "Classifies support tickets, identifies missing fields, and drafts replies for human review",
			Command:          "python3",
			Args:             []string{"backend/agents/support_ticket_triage_agent/cli.py"},
			Timeout:          salesAgentTimeout,
			WorkingDir:       ".",
			ConcurrencyLimit: 5,
			AgentType:        "support_ticket_triage",
		},
		"blog": {
			Name:             "Blog Agent",
			Description:      "Generates structured blog outlines and drafts for marketing teams",
			Command:          "python3",
			Args:             []string{"backend/agents/blog_agent/cli.py"},
			Timeout:          blogAgentTimeout,
			WorkingDir:       ".",
			ConcurrencyLimit: 5,
			AgentType:        "blog",
		},
		// Add more tools here as needed...
		// Example:
		// "seo-analyzer": {
		//     Name:             "SEO Analyzer",
		//     Description:      "Analyze website SEO and provide recommendations",
		//     Command:          "python",
		//     Args:             []string{"agents/seo_analyzer_agent/cli.py"},
		//     Timeout:          2 * time.Minute,
		//     WorkingDir:       ".",
		//     ConcurrencyLimit: 3,
		//     AgentType:        "seo-analyzer",
		// },
	}
}

// GetTool retrieves a tool by name
func GetTool(name string) (ToolConfig, bool) {
	tool, exists := Registry[name]
	return tool, exists
}

// ListTools returns all available tools
func ListTools() []ToolConfig {
	tools := make([]ToolConfig, 0, len(Registry))
	for _, tool := range Registry {
		tools = append(tools, tool)
	}
	return tools
}

// GetToolByAgentType finds a tool by its agent type (used for backward compatibility)
func GetToolByAgentType(agentType string) (ToolConfig, bool) {
	for _, tool := range Registry {
		if tool.AgentType == agentType {
			return tool, true
		}
	}
	return ToolConfig{}, false
}
