package integrations

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

type FreshdeskClient struct {
	domain string
	apiKey string
	http   *http.Client
}

func NewFreshdeskClientFromEnv() (*FreshdeskClient, error) {
	domain := strings.TrimSpace(os.Getenv("FRESHDESK_DOMAIN"))
	apiKey := strings.TrimSpace(os.Getenv("FRESHDESK_API_KEY"))
	if domain == "" || apiKey == "" {
		return nil, errors.New("missing FRESHDESK_DOMAIN or FRESHDESK_API_KEY")
	}
	// allow full domain or host; normalize to host only
	domain = strings.TrimPrefix(domain, "https://")
	domain = strings.TrimPrefix(domain, "http://")
	domain = strings.TrimSuffix(domain, "/")

	return &FreshdeskClient{
		domain: domain,
		apiKey: apiKey,
		http: &http.Client{
			Timeout: 20 * time.Second,
		},
	}, nil
}

func (c *FreshdeskClient) baseURL() string {
	return fmt.Sprintf("https://%s/api/v2", c.domain)
}

func (c *FreshdeskClient) authHeader() string {
	// Freshdesk: API key as username, password = X
	raw := c.apiKey + ":X"
	return "Basic " + base64.StdEncoding.EncodeToString([]byte(raw))
}

func (c *FreshdeskClient) doJSON(ctx context.Context, method string, url string, out any) error {
	req, err := http.NewRequestWithContext(ctx, method, url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", c.authHeader())
	req.Header.Set("Accept", "application/json")

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("freshdesk api error: status=%d body=%s", resp.StatusCode, string(body))
	}

	if out == nil {
		return nil
	}
	return json.Unmarshal(body, out)
}

// GetTicket returns the raw ticket JSON as map.
func (c *FreshdeskClient) GetTicket(ctx context.Context, ticketID string) (map[string]any, error) {
	var out map[string]any
	err := c.doJSON(ctx, "GET", c.baseURL()+"/tickets/"+ticketID, &out)
	return out, err
}

// ListConversations returns the raw conversations JSON array as []map[string]any.
func (c *FreshdeskClient) ListConversations(ctx context.Context, ticketID string) ([]map[string]any, error) {
	var out []map[string]any
	err := c.doJSON(ctx, "GET", c.baseURL()+"/tickets/"+ticketID+"/conversations", &out)
	return out, err
}
