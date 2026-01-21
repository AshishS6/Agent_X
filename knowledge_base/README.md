# Knowledge Base Documentation

## Current Knowledge Base Contents

### Fintech Knowledge Base (`fintech`)

**Total Documents: 8 chunks**

#### 1. General Fintech Overview (2 chunks)
- Fintech definition and key areas
- Regulatory considerations
- Market trends

#### 2. Open Money Company Overview (3 chunks)
- Company identity and positioning
- Core focus areas
- Target customers
- Primary capabilities
- What Open Money is NOT
- Operating geography and regulatory context

#### 3. Zwitch Company Overview (3 chunks)
- Company identity and positioning
- Core focus areas (BaaS, APIs)
- Target customers
- Primary capabilities
- What Zwitch is NOT
- Operating geography and regulatory context

## How to Use

### In the Frontend

1. **Select Fintech Assistant** from the Assistant Selector dropdown
2. **Ask questions** like:
   - "What is Open Money?"
   - "Is Zwitch a bank?"
   - "Who are Zwitch's target customers?"
   - "What are the differences between Open Money and Zwitch?"
   - "What is Banking-as-a-Service?"

### Testing Questions

Try these to verify RAG is working:

✅ **Should find answers in your documents:**
- "What is Open Money?"
- "What does Zwitch do?"
- "Is Open Money a consumer banking app?"
- "What is Banking-as-a-Service?"
- "Who are Open Money's target customers?"

⚠️ **May use general knowledge (not in documents):**
- "What is the stock price of Apple?"
- "How do I invest in mutual funds?"

## Adding More Documents

### Method 1: Via API

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "file=@knowledge_base/openmoney/products.md" \
  -F "knowledge_base=fintech"
```

### Method 2: Batch Upload Script

Create a script to upload all files:

```bash
#!/bin/bash
for file in knowledge_base/**/*.md; do
  echo "Uploading $file..."
  curl -X POST http://localhost:8000/api/ingest \
    -F "file=@$file" \
    -F "knowledge_base=fintech"
done
```

## Viewing Stored Data

```bash
cd backend
python3 view_fintech_data.py
```

## Next Steps (Recommended)

Add these documents in order:

1. `knowledge_base/openmoney/products.md`
2. `knowledge_base/openmoney/onboarding_flow.md`
3. `knowledge_base/openmoney/compliance_regulatory.md`
4. `knowledge_base/zwitch/products.md`
5. `knowledge_base/zwitch/onboarding_flow.md`
6. `knowledge_base/zwitch/compliance_regulatory.md`

## File Structure

```
knowledge_base/
├── openmoney/
│   ├── company_overview.md ✅ (Ingested)
│   ├── products.md (To add)
│   ├── onboarding_flow.md (To add)
│   └── compliance_regulatory.md (To add)
└── zwitch/
    ├── company_overview.md ✅ (Ingested)
    ├── products.md (To add)
    ├── onboarding_flow.md (To add)
    └── compliance_regulatory.md (To add)
```

