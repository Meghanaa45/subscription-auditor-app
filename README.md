# Subscription Auditor

**Subscription Auditor** analyzes bank and credit-card statement CSV exports to identify recurring subscriptions, detect silent price increases, estimate potential cancellation savings, and answer plain-language questions about the audit results using an LLM agent grounded in the actual detection output.

```text
Upload CSV → Detect subscriptions → Analyze price changes → "Ask the Auditor"
```

## Why This Is More Than `groupby("merchant")`

Real-world bank exports are messy. The same merchant can appear under different names across transactions, for example:

```text
NETFLIX.COM
NETFLIX LOS GATOS CA
NFLX*STREAMING
```

Billing dates can drift, subscription prices can change, and not every recurring transaction is necessarily a subscription. For example, a weekly coffee purchase may repeat frequently but still have irregular timing and amounts.

Subscription Auditor explicitly handles these challenges through:

* Merchant name normalization
* Recurrence and billing-interval detection
* Amount consistency analysis
* Price-change detection
* Subscription classification
* Cancellation-savings estimation
* Evaluation against ground-truth data
* LLM-based question answering grounded in detected results

The core detection logic is implemented under `backend/app/core/`.

---

# Architecture

```text
backend/
│
├── app/
│   ├── core/
│   │   └── Detection engine
│   │       ├── CSV ingestion
│   │       ├── Merchant normalization
│   │       ├── Recurrence detection
│   │       ├── Pricing analysis
│   │       └── Evaluation
│   │
│   ├── agent/
│   │   └── Azure OpenAI tool-calling agent
│   │       ├── Reads actual audit results
│   │       ├── Answers user questions
│   │       └── Prevents unsupported/invented numbers
│   │
│   ├── api/
│   │   ├── FastAPI routes
│   │   ├── Request/response schemas
│   │   └── In-memory audit result store
│   │
│   ├── cli.py
│   │   └── Optional terminal-based entry point
│   │
│   └── main.py
│       └── FastAPI application
│
├── scripts/
│   └── generate_synthetic_data.py
│       └── Generates synthetic transactions and ground truth
│
├── tests/
│   └── Pytest test suite
│
├── data/
│   └── Sample and evaluation data
│
└── sample_output/
    └── Example audit report


frontend/
│
└── src/
    ├── App.jsx
    │   └── Main application layout
    │
    ├── components/
    │   ├── UploadPanel.jsx
    │   │   └── CSV upload / drag-and-drop
    │   │
    │   ├── StatementTotal.jsx
    │   │   └── Summary figures
    │   │
    │   ├── LedgerList.jsx
    │   │   └── Detected subscription list
    │   │
    │   ├── AuditMark.jsx
    │   │   └── Visual indicator for price increases
    │   │
    │   └── ChatPanel.jsx
    │       └── "Ask the Auditor" chat interface
    │
    └── api/
        └── client.js
            └── Backend API client
```

### Core Design

The detection engine is completely independent of the API and LLM agent.

```text
                 ┌─────────────────────┐
                 │    Bank CSV File    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Ingestion Layer   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Merchant Normalizer │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Recurrence Detector │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Pricing Analysis   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Audit Results     │
                 └──────┬─────────┬────┘
                        │         │
                        │         ▼
                        │   ┌───────────────┐
                        │   │ Azure OpenAI  │
                        │   │ Agent         │
                        │   └───────┬───────┘
                        │           │
                        ▼           ▼
                 ┌────────────────────────┐
                 │       Frontend         │
                 │ Dashboard + Chat       │
                 └────────────────────────┘
```

The same tested detection engine can therefore be used through:

* CLI
* FastAPI
* Frontend
* Python notebooks
* Automated evaluation

The LLM is **not responsible for detecting subscriptions**. It reads the detector's results through defined tools and explains those results to the user.

---

# Features

## 1. Subscription Detection

Identifies recurring transactions by analyzing:

* Merchant identity
* Transaction frequency
* Billing intervals
* Transaction amounts
* Historical occurrences

The system requires at least **three occurrences** before classifying a merchant as recurring.

This reduces false positives caused by short transaction histories.

---

## 2. Merchant Normalization

Different transaction descriptions may represent the same merchant.

For example:

```text
NETFLIX.COM
NETFLIX LOS GATOS CA
NFLX*STREAMING
```

The normalization process attempts to group these variations into a common merchant identity before recurrence analysis.

This prevents the system from treating every description variation as a separate merchant.

---

## 3. Recurrence Detection

The system analyzes transaction timing and amounts to distinguish potential subscriptions from ordinary repeated spending.

For example:

```text
Netflix
01-Jan   $15.99
01-Feb   $15.99
02-Mar   $15.99
01-Apr   $15.99
```

This pattern is consistent with a recurring subscription.

In contrast:

```text
Coffee Shop
02-Jan   $4.50
08-Jan   $7.20
13-Jan   $3.80
27-Jan   $6.90
```

Although the merchant repeats, the irregular timing and amounts make it less likely to be a subscription.

---

## 4. Silent Price Increase Detection

The system compares historical subscription amounts to identify potential price increases.

Example:

```text
Netflix
Jan → $15.99
Feb → $15.99
Mar → $15.99
Apr → $17.99
```

The system can flag the increase and calculate the additional recurring cost.

---

## 5. Cancellation Savings

For detected subscriptions, the application estimates potential savings if the user cancels them.

Example:

```text
Monthly subscription: $17.99
Estimated annual cost: $215.88

Potential annual savings:
$215.88
```

---

# Ask the Auditor

The project includes an LLM-powered question-answering layer using **Azure OpenAI**.

Users can ask questions such as:

```text
Which subscriptions cost me the most?

Which subscriptions increased in price?

How much could I save if I cancel the subscriptions?

Which subscriptions have the largest recent price increases?
```

The important design principle is that the LLM does **not** independently calculate or invent financial results.

Instead:

```text
User Question
      ↓
Azure OpenAI Agent
      ↓
Tool Call
      ↓
Actual Audit Results
      ↓
Grounded Answer
```

The agent uses tools that read the actual detection output.

This means the LLM acts primarily as a **natural-language interface over the audit results**, rather than as the source of truth for the financial calculations.

---

# Supported Bank CSV Formats

The application supports automatic format detection based on CSV column headers.

Supported formats:

* Chase
* Bank of America
* Discover
* Generic format:

  * `date`
  * `description`
  * `amount`

### American Express

American Express requires special handling because its headers can match Bank of America's format while using a different sign convention for charges.

Therefore, Amex cannot always be detected safely from headers alone.

Use:

```bash
--bank amex
```

when running the CLI with an American Express statement.

Alternatively, use the generic CSV format through the API.

This is intentionally designed as a **fail-safe rather than making an unsafe format assumption**.

---

# Setup

## 1. Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

On Windows, create `.env` manually if `cp` is unavailable.

Generate sample data:

```bash
python scripts/generate_synthetic_data.py
```

Run the test suite:

```bash
pytest tests/ -v
```

The project currently contains **37 tests** covering the core detection logic, agent tools, and API endpoints.

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

# Azure OpenAI Configuration

Azure OpenAI is optional.

The application works without Azure OpenAI, but the **Ask the Auditor** chat functionality will be disabled.

Add the following variables to `.env`:

```dotenv
AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-key"
AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
```

### Important

`AZURE_OPENAI_DEPLOYMENT` is the **deployment name you configured in Azure**, not necessarily the underlying model name.

For example:

```text
Model:
GPT-4o

Deployment name:
subscription-auditor-prod
```

In this case:

```dotenv
AZURE_OPENAI_DEPLOYMENT="subscription-auditor-prod"
```

If Azure OpenAI credentials are not configured:

```text
/api/health
```

reports:

```json
{
  "agent_configured": false
}
```

The rest of the application continues to work normally.

---

# Frontend

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the environment file:

```bash
cp .env.example .env
```

The default API URL points to:

```text
http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

You can either:

* Upload your own bank CSV
* Drag and drop a CSV file
* Use the sample data to immediately run an audit

---

# Running Tests

From the backend directory:

```bash
cd backend
pytest tests/ -v
```

The test suite currently contains **37 tests** covering:

* Merchant normalization
* Recurrence detection
* Interval analysis
* Amount analysis
* Irregular recurring spending
* Price-change detection
* Savings calculations
* Evaluation against ground truth
* CSV ingestion
* Bank-format handling
* Agent tool functions
* API endpoints

The chat endpoint tests mock the agent call, so real Azure OpenAI credentials are not required to run the test suite.

---

# Using the Auditor Without the Frontend

The backend also provides a CLI interface.

```bash
cd backend

python -m app.cli data/sample_transactions.csv \
    --evaluate data/ground_truth.csv
```

This allows the core detection engine to be used without running the React frontend.

---

# Project Evaluation

Synthetic transaction data and corresponding ground-truth data can be generated with:

```bash
python scripts/generate_synthetic_data.py
```

This allows the detection engine to be evaluated against known expected results.

The evaluation workflow helps measure whether the system correctly identifies recurring transactions and avoids incorrectly classifying irregular spending as subscriptions.

---

# Deployment

The application is designed as two independently deployable services.

## Backend

The backend is a Python ASGI application and can be deployed to platforms such as:

* Render
* Railway
* Fly.io
* AWS EC2
* Any VM running Uvicorn/Gunicorn

Set environment variables through the deployment platform rather than committing a `.env` file.

Required configuration includes:

```text
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT
AZURE_OPENAI_API_VERSION
FRONTEND_ORIGIN
```

`FRONTEND_ORIGIN` should contain the deployed frontend URL so that the backend can configure CORS appropriately.

---

## Frontend

The React frontend can be deployed to static hosting platforms such as:

* Vercel
* Netlify
* Cloudflare Pages
* Amazon S3 + CloudFront

Build the application:

```bash
npm run build
```

This generates the production build in:

```text
dist/
```

Configure the backend URL through the frontend environment variable:

```text
VITE_API_URL
```

The value should point to the deployed backend API.

---

# Design Decisions

## Why not simply group by merchant?

A simple implementation might do:

```python
df.groupby("merchant")
```

However, this can produce incorrect results because:

1. Merchant names may vary.
2. Transaction dates may not occur on exactly the same day.
3. Subscription prices may change.
4. Recurring purchases are not always subscriptions.
5. Short transaction histories can create false positives.

Subscription Auditor therefore separates the process into multiple stages:

```text
CSV Ingestion
      ↓
Merchant Normalization
      ↓
Recurrence Analysis
      ↓
Subscription Classification
      ↓
Price Analysis
      ↓
Savings Calculation
      ↓
Audit Report
      ↓
LLM Question Answering
```

---

# Design Principles

### 1. Deterministic detection

The core financial calculations are performed by deterministic application logic rather than by the LLM.

### 2. Grounded AI

The LLM receives access to actual audit results through defined tools.

### 3. Separation of concerns

The detection engine does not depend on FastAPI, React, or Azure OpenAI.

### 4. Testability

The core logic can be tested independently from the API and LLM.

### 5. Fail-safe bank detection

When a bank format cannot be safely distinguished, the application requires explicit input rather than silently making an assumption.

---

# Known Limitations

### 1. Minimum transaction history

A merchant must have at least **three occurrences** before it can be classified as recurring.

This reduces false positives but means newly started subscriptions may not be detected immediately.

### 2. In-memory audit storage

The current audit store:

```text
backend/app/api/store.py
```

is process-local.

This means audit results are cleared when the backend process restarts.

This is acceptable for a demo or single-user deployment.

For a production multi-user application, this component should be replaced with a persistent database.

The application intentionally keeps this storage behind a clear interface so it can be replaced without changing the detection engine.

### 3. Bank format ambiguity

Some banks can share identical CSV headers while using different amount/sign conventions.

For example, Bank of America and American Express may require different interpretation of transaction amounts.

The application therefore requires explicit bank selection when automatic detection is not safe.

---

# End-to-End Flow

```text
                  USER
                   │
                   ▼
             Upload CSV
                   │
                   ▼
          CSV Ingestion Layer
                   │
                   ▼
        Merchant Normalization
                   │
                   ▼
        Recurrence Detection
                   │
                   ▼
       Subscription Detection
                   │
                   ▼
         Price-Change Analysis
                   │
                   ▼
        Savings Calculation
                   │
                   ▼
            Audit Results
              │         │
              │         │
              ▼         ▼
          Dashboard   LLM Agent
                        │
                        ▼
                 Tool Calls
                        │
                        ▼
                 Audit Results
                        │
                        ▼
                Grounded Answer
```

---

# Example User Experience

```text
1. Upload bank statement CSV
           ↓
2. System normalizes merchant names
           ↓
3. System detects recurring transactions
           ↓
4. System identifies subscription price changes
           ↓
5. System calculates potential savings
           ↓
6. Results appear in the dashboard
           ↓
7. User asks:
   "How much could I save by cancelling subscriptions?"
           ↓
8. Agent retrieves the actual audit results
           ↓
9. Agent returns a grounded answer
```

---

# Tech Stack

### Backend

* Python
* FastAPI
* Pandas
* Pytest
* Azure OpenAI

### Frontend

* React
* JavaScript
* Vite

### AI

* Azure OpenAI
* Tool calling
* Grounded question answering

### Data Processing

* CSV ingestion
* Merchant normalization
* Recurrence analysis
* Price-change detection
* Savings calculations
* Synthetic data generation
* Ground-truth evaluation

---

# Summary

Subscription Auditor is a financial transaction analysis application that combines **deterministic data processing with grounded LLM interaction**.

The core system identifies recurring subscriptions, detects price increases, and estimates potential savings from cancellation. The LLM layer then provides a natural-language interface for exploring those results while relying on the application's actual audit data rather than generating unsupported financial figures.

```text
Messy Financial Data
        ↓
Normalize
        ↓
Detect Recurring Transactions
        ↓
Analyze Price Changes
        ↓
Calculate Savings
        ↓
Generate Audit Results
        ↓
Grounded LLM Interaction
        ↓
Actionable Financial Insights
```
