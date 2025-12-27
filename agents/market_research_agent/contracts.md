# Market Research Agent - API Contracts

**Purpose**: This document defines the input/output contracts that MUST NOT BREAK during refactoring.

---

## Task Names (Redis Queue)

The following task names are supported:

- `site_scan`
- `comprehensive_site_scan`
- `monitor_url`
- `analyze_competitor`
- `track_trends`
- `compliance_check`
- `generate_report`

---

## Input Schema (Redis Task Payload)

```json
{
  "taskId": "string (UUID)",
  "action": "string (task name from above)",
  "input": {
    // Action-specific fields
  },
  "userId": "string (optional)",
  "priority": "string (optional, default: 'medium')"
}
```

### Action-Specific Input Fields

#### `comprehensive_site_scan`
```json
{
  "url": "string (required)",
  "business_name": "string (optional)"
}
```

#### `monitor_url`
```json
{
  "url": "string (required)",
  "keywords": "string (optional, comma-separated)",
  "max_pages": "number (optional, default: 0)",
  "depth": "number (optional, default: 1)",
  "respect_robots_txt": "boolean (optional, default: true)",
  "delay": "number (optional, default: 1.0)"
}
```

#### `analyze_competitor`
```json
{
  "company_name": "string (required)"
}
```

#### `track_trends`
```json
{
  "topic": "string (required)"
}
```

#### `compliance_check`
```json
{
  "topic": "string (required)",
  "industry": "string (optional, default: 'general')"
}
```

#### `generate_report`
```json
{
  "research_data": "string (required, JSON or text)",
  "report_type": "string (optional, default: 'summary')",
  "format": "string (optional, default: 'markdown')"
}
```

---

## Output Schema (Database Task Result)

### Task Status Updates

```json
{
  "status": "processing | completed | failed",
  "output": "object (when completed)",
  "error": "string (when failed)"
}
```

### Comprehensive Site Scan Output

**CRITICAL**: The output MUST be wrapped in a `comprehensive_site_scan` key for frontend compatibility.

```json
{
  "comprehensive_site_scan": {
    "url": "string",
    "business_name": "string",
    "scan_timestamp": "ISO 8601 datetime",
    "compliance": {
      "general": {
        "pass": "boolean",
        "alerts": [
          {
            "code": "string (e.g., 'LIVENESS_FAIL')",
            "type": "string (e.g., 'Availability')",
            "description": "string"
          }
        ],
        "actions_needed": [
          {
            "description": "string"
          }
        ]
      },
      "payment_terms": {
        "pass": "boolean",
        "alerts": "array",
        "actions_needed": "array"
      }
    },
    "policy_details": {
      "home_page": {
        "found": "boolean",
        "url": "string",
        "status": "string"
      },
      "privacy_policy": { "found": "boolean", "url": "string", "status": "string" },
      "shipping_delivery": { "found": "boolean", "url": "string", "status": "string" },
      "returns_refund": { "found": "boolean", "url": "string", "status": "string" },
      "terms_condition": { "found": "boolean", "url": "string", "status": "string" },
      "contact_us": { "found": "boolean", "url": "string", "status": "string" },
      "about_us": { "found": "boolean", "url": "string", "status": "string" },
      "faq": { "found": "boolean", "url": "string", "status": "string" },
      "product": { "found": "boolean", "url": "string", "status": "string" }
    },
    "business_details": {
      "extracted_business_name": "string"
    },
    "content_risk": {
      "dummy_words_detected": "boolean",
      "dummy_words": "array of strings",
      "restricted_keywords_found": [
        {
          "category": "string",
          "keyword": "string"
        }
      ],
      "risk_score": "number"
    },
    "mcc_codes": {
      "primary_mcc": {
        "category": "string",
        "subcategory": "string",
        "mcc_code": "string",
        "description": "string",
        "confidence": "number",
        "keywords_matched": "number"
      },
      "secondary_mcc": "object (same structure as primary_mcc, nullable)",
      "all_matches": "array of MCC objects (top 10)"
    },
    "product_details": {
      "has_products": "boolean",
      "has_pricing": "boolean",
      "has_cart": "boolean",
      "ecommerce_platform": "boolean"
    }
  }
}
```

---

## Conversation Messages (Database)

```json
{
  "agent_id": "string",
  "task_id": "string (UUID)",
  "role": "string (user | assistant | system)",
  "content": "string"
}
```

---

## Critical Rules

1. **DO NOT** change the root key `comprehensive_site_scan` in the output
2. **DO NOT** change field names in the output schema
3. **DO NOT** remove existing fields (only add new ones)
4. **DO NOT** change task names
5. **ALWAYS** wrap comprehensive_site_scan output in the root key
6. **ALWAYS** return valid JSON from tools
7. **ALWAYS** update task status to "processing" before execution
8. **ALWAYS** update task status to "completed" or "failed" after execution

---

## Version History

- **v1.0** (Current): Initial contract documentation
