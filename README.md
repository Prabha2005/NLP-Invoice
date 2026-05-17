## Backend Integration and API Development

# What I Worked On

1. Set up the FastAPI backend architecture
2. Implemented REST API routes for rule parsing and validation
3. Integrated Ollama with the backend pipeline
4. Connected the parser, compiler, and validator modules
5. Implemented XML invoice upload handling
6. Structured PASS/FAIL validation responses
7. Added Swagger/OpenAPI testing support
8. Stabilized parser and validation pipeline for demo reliability
9. Tested valid and invalid UBL XML invoices

# Backend Setup Steps

**1. Clone Repository**
```bash
git clone https://github.com/Prabha2005/NLP-Invoice.git
cd NLP-Invoice
```

**2. Move to Development Branch**
```bash
git checkout dev
git pull origin dev
```

**3. Create Feature Branch**
```bash
git checkout -b feature-fastapi-routes
```

**4. Backend Setup**
```bash
cd backend
python -m venv .venv
# Activate virtual environment:
.venv\Scripts\activate
```
**5. Install Requirements**
```bash
pip install -r requirements.txt
```

**6. Install Ollama Python Package**
```bash
pip install ollama
```

**7. Install Ollama Runtime**
# Download and install:
Ollama Windows Installer

**8. Pull LLM Model**
```bash
ollama pull llama3.2
```
**9. Run Backend Server**
```bash
uvicorn app.main:app --reload
```

# API Testing
Swagger/OpenAPI available at:
http://127.0.0.1:8000/docs

# API Endpoints Implemented

| **Method** | **Endpoint**          | **Purpose**                                    |
| -----------| --------------------- | ---------------------------------------------- |
| POST       | `/api/rules/parse`    | Parse English rule into IR                     |
| POST       | `/api/rules/validate` | Validate XML against IR                        |
| POST       | `/api/rules/run`      | Full validation pipeline                       |
| GET        | `/health`             | Backend health check                           |

# Rule Text Examples Used for Testing

**Example 1**
Invoice must contain IssueDate
**Expected:**
PASS
**Using:**
pint-ae-invoice-valid-01.xml

**Example 2**
Invoice must contain DueDate
**Expected:**
FAIL
**Using:**
pint-ae-invoice-invalid-01.xml

**Example 3**
DocumentCurrencyCode must equal AED
**Expected:**
PASS

**Example 4**
Invoice must contain TaxTotal
**Expected:**
PASS

**Example 5**
Invoice must contain BuyerReference
**Expected:**
FAIL

# Example Successful API Response
```bash
{
  "status": "PASS",
  "rule_text": "Invoice must contain IssueDate",
  "summary": {
    "total_checks": 1,
    "passed_checks": 1,
    "failed_checks": 0
  }
  }
```

# Current Working Features

1. Plain-English rule parsing
2. Typed IR generation
3. XML invoice validation
4. Structured PASS/FAIL output
5. Swagger/OpenAPI testing
6. Local LLM execution using Ollama
7. XML upload and validation pipeline

# Current Hosting / Runtime

| **Component** | **Hosting**                      |                                    
| --------------| ---------------------------------|
| Backend API   | Local FastAPI server             |                    
| LLM Runtime   | Local Ollama runtime             |                        
| API Docs      | Swagger UI                       |                     
| Frontend      | Next.js local development server |                   

# Ports Used

| **Service**      | **Port**   |                                    
| --------------   | -----------|
| FastAPI Backend  | 8000       |                    
| Next.js Frontend | 3000       |                        
| API Docs         | 8000/docs  |                     

# Validation Flow

Plain-English Rule
        ↓
Ollama Parser
        ↓
Typed IR (JSON)
        ↓
Deterministic Validation Engine
        ↓
XML Invoice Validation
        ↓
PASS / FAIL Response