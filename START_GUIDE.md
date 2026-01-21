# 🚀 Quick Start Guide - Backend & Frontend

## Step-by-Step Instructions

### Step 1: Start Docker Services (Database)

```bash
# From Agent_X root directory
docker-compose up -d

# Verify services are running
docker-compose ps
```

You should see:
- ✅ `agentx-postgres` - running
- ✅ `agentx-redis` - running

**Note**: Wait ~30 seconds for PostgreSQL to fully initialize.

---

### Step 2: Start the Go Backend

```bash
# Navigate to backend directory
cd backend

# Start the server (with hot reload if air is installed)
make dev

# OR if make dev doesn't work:
go run ./cmd/server
```

**Expected Output:**
```
✅ Database connected
📁 Project root: /path/to/Agent_X
⚡ Executor initialized (global: 10, per-tool default: 5)
🚀 Server starting on port 3001
```

**Backend will be available at:** http://localhost:3001

---

### Step 3: Verify Backend Health

In a **new terminal**, test the backend:

```bash
# Health check
curl http://localhost:3001/api/monitoring/health

# List agents
curl http://localhost:3001/api/agents

# Expected response should show agents including "market_research"
```

---

### Step 4: Start the Frontend

In a **new terminal** (keep backend running):

```bash
# From Agent_X root directory
npm install  # First time only
npm run dev
```

**Frontend will be available at:** http://localhost:5173

---

### Step 5: Use Site Scan from Frontend

1. **Open your browser** and go to: http://localhost:5173

2. **Navigate to Market Research Agent:**
   - Click on **"Market Research"** in the sidebar
   - Or go directly to: http://localhost:5173/market-research

3. **Start a Site Scan:**
   - Click **"+ New Research Report"** button
   - Select **"Site Scan"** from the action dropdown
   - Enter a website URL (e.g., `https://example.com`)
   - Optionally enter a business name
   - Click **"Start Research"** or **"Execute"**

4. **Wait for Results:**
   - The scan typically takes 1-3 minutes
   - You'll see a task ID and status updates
   - Results will appear automatically when complete

5. **View Results:**
   - The frontend will display:
     - Compliance checks (SSL, liveness, domain age)
     - Policy pages found (privacy, terms, returns, etc.)
     - MCC codes (Merchant Category Codes)
     - Tech stack detection
     - SEO analysis
     - Business details

6. **Download Report:**
   - Click the **"Download Report"** button
   - Choose format: PDF, JSON, or Markdown

---

## Troubleshooting

### Backend won't start

```bash
# Check if port 3001 is in use
lsof -i :3001

# Check database connection
docker-compose ps
docker-compose logs postgres

# Verify .env file has correct DATABASE_URL
cat backend/.env | grep DATABASE_URL
```

### Frontend can't connect to backend

```bash
# Verify backend is running
curl http://localhost:3001/api/monitoring/health

# Check CORS settings in backend/.env
# Should include: CORS_ORIGINS=http://localhost:5173
```

### Site scan fails

```bash
# Check Python dependencies
cd backend/agents
pip install -r requirements.txt

# Test agent directly
cd market_research_agent
python3 cli.py --input '{"action": "site_scan", "url": "https://example.com"}'
```

### Database connection errors

```bash
# Restart Docker services
docker-compose down
docker-compose up -d

# Check database logs
docker-compose logs postgres
```

---

## API Endpoints Reference

### Execute Site Scan (via API)

```bash
curl -X POST http://localhost:3001/api/agents/market_research/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "comprehensive_site_scan",
    "input": {
      "topic": "https://example.com",
      "business_name": "Example Inc"
    }
  }'
```

### Check Task Status

```bash
# Replace {task-id} with the ID from the response above
curl http://localhost:3001/api/tasks/{task-id}
```

---

## Quick Commands Summary

```bash
# Terminal 1: Docker services
docker-compose up -d

# Terminal 2: Backend
cd backend && make dev

# Terminal 3: Frontend  
npm run dev

# Terminal 4: Test API
curl http://localhost:3001/api/monitoring/health
```

---

## Environment Variables

Make sure `backend/.env` has:

```env
PORT=3001
DATABASE_URL=postgres://postgres:dev_password@localhost:5432/agentx?sslmode=disable
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

**Ready to scan websites!** 🎉
