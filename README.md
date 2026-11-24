# BusinessPulse AI

**Unified Business Intelligence & Predictive Decision Platform**

> Understand Your Business. Predict What’s Next. Make Smarter Decisions.

---

## 1. Executive Summary

**BusinessPulse AI** is an enterprise-grade AI decision-support platform designed to transform fragmented business data into forward-looking intelligence. Traditional Business Intelligence systems merely report what happened in the past. BusinessPulse AI analyzes historical data, trains machine learning models, forecasts future risks, generates explainable recommendations, and allows human-controlled execution into external systems.

### Core Capabilities:
1. **High-Throughput Data Ingestion Engine:** Vectorized CSV/Excel parsing and dry-run schema validation with auto-column mapping (supporting standard and Kaggle-style schemas like `StockCode`, `CustomerID`, `InvoiceDate`), row-level error diagnostics, and batched bulk database ingestion.
2. **SupplyChain Intelligence:** Multi-horizon demand forecasting (7, 14, 30 days) using XGBoost, inventory depletion and stockout risk prediction, supplier reliability scorecards, and supply chain shock simulations.
3. **Revenue Intelligence:** Cashflow revenue forecasting with 95% confidence intervals, customer churn classification using class-balanced XGBoost, RFM behavioral customer segmentation using K-Means, and revenue elasticity simulations.
4. **Decision & Policy Engine:** Deterministic rule evaluation converting analytical findings into actionable recommendations with grounded AI explanation synthesis.
5. **Human Approval & Governance:** Role-based human-in-the-loop approval workflows with idempotent action execution (`X-Idempotency-Key`).
6. **Modern Enterprise Dashboard:** React 18 + TypeScript + Vite + Tailwind CSS dashboard with Light/Dark theme switching, an interactive **How to Use** onboarding guide, Recharts visualizations, and zero mock data.

---

## 2. Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | FastAPI (Python 3.11), Pydantic v2, Starlette |
| **Database & ORM** | PostgreSQL 16 (production), SQLite (zero-config local test fallback), SQLAlchemy 2.0 |
| **Machine Learning** | XGBoost, Scikit-Learn (Isolation Forest, K-Means, RFM), NumPy, Pandas |
| **Authentication** | JWT (JSON Web Tokens), Passlib (Bcrypt), RBAC with 6 hierarchical enterprise roles |
| **Frontend Framework** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts |
| **DevOps & Containers** | Docker, Docker Compose, Alembic Database Migrations |
| **Testing** | Pytest, Pytest-Asyncio, HTTP TestClient (40 automated tests, 100% pass rate) |

---

## 3. System Architecture

```
[ ERP / CRM / CSV Data Feeds ]
              │
              ▼
   [ Data Ingestion Engine ] ──► (Dry-Run Validation, Mapping, Deduplication)
              │
              ▼
    [ PostgreSQL Database ] ──► (Multi-Tenant Isolation via organization_id)
              │
      ┌───────┴────────────────────────┐
      ▼                                ▼
[ SupplyChain ML Pipeline ]   [ Revenue ML Pipeline ]
  • XGBoost Forecaster          • XGBoost Cashflow Forecaster
  • Seasonal Naive Baseline     • 95% Confidence Bounds
  • Inventory Risk Depletion    • XGBoost Churn Classifier
  • Supplier Scorecards         • K-Means RFM Segmentation
      │                                │
      └───────┬────────────────────────┘
              ▼
   [ Decision & Policy Engine ]
              │
              ├──► [ Grounded AI Explainer (Strict Evidence Guardrails) ]
              ▼
   [ Human Approval & Governance ]
              │
              ▼ (Approved)
  [ Idempotent Action Dispatcher ] ──► [ External Mock ERP / CRM ]
```

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for containerized deployment)

### Option A: Local Development Run

#### 1. Backend Setup:
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run full automated test suite (40 tests)
PYTHONPATH=. pytest tests/

# Seed realistic demo dataset (PRD Section 29 Scenario)
python scripts/generate_demo_data.py

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

#### 2. Frontend Setup:
```bash
cd frontend
npm install

# Build production bundle
npm run build

# Start Vite development server
npm run dev
```
Web Application will be available at: `http://localhost:5173`

---

### Option B: Docker Compose Run

Run the complete multi-container stack (PostgreSQL, Backend API, and Frontend):
```bash
docker-compose up --build -d
```

---

## 5. Step-by-Step Usage Walkthrough

1. **Create Account or Sign In**: Navigate to `http://localhost:5173/login` and register a new organization (new organization founders default to `Admin`) or sign in.
2. **Follow the Built-In Guide**: Click the **How to Use** button in the top navigation bar (or follow the Quick Start card on **Overview**) and toggle **Light / Dark** mode anytime.
3. **Data Sources & Ingest (`/data-sources`)**:
   - Select a target schema (e.g., **Sales Transactions**).
   - Choose a `.csv` / `.xlsx` file (including large 500k+ row datasets).
   - Click **Dry-Run Validation Preview** to inspect auto-detected column mappings and row-level errors.
   - Click **Confirm & Commit Ingestion** to bulk-load valid records into your organization.
4. **Business Entities (`/entities`)**: Browse and search auto-populated Products, Customers, Suppliers, and Warehouses.
5. **SupplyChain Intelligence (`/supply-chain`)**:
   - Inspect inventory levels, stockout risks, and supplier scorecards.
   - Select a product and click **Re-run ML Forecaster** to generate 7/14/30-day XGBoost demand forecasts.
6. **Revenue Intelligence (`/revenue`)**:
   - View monthly revenue velocity, 30-day cashflow forecasts with 95% confidence bands, Churn Radar predictions, and K-Means RFM customer segments.
7. **Recommendations & AI Explanation (`/recommendations`)**:
   - Click **Run Decision Engine** to generate prioritized actions, and click **Explain with AI** to inspect grounded evidence.
8. **What-If Simulations (`/simulations`)**:
   - Stress-test demand surges, supplier delays, inventory loss, and revenue/churn elasticity using interactive sliders.
9. **Approval Center (`/approvals`)**:
   - Review pending AI recommendations, **Approve** or **Reject** with comments, and **Execute** approved actions idempotently.

---

## 6. Automated Test Suite

Run the complete test suite:
```bash
cd backend
PYTHONPATH=. venv/bin/pytest tests/ -v
```

Test Breakdown:
- **Unit Tests:** Password hashing, JWT token verification, RBAC role dependencies (5 tests).
- **Data Ingestion API:** Schema detection, dry-run validation, row-level error reporting, CSV/Excel parsing (9 tests).
- **Business Entities API:** CRUD, aggregated sales units, revenue metrics, inventory per warehouse (4 tests).
- **Supply Chain API:** Demand forecasting, WAPE baseline comparison, stockout calculations, supplier scorecards, what-if simulations (5 tests).
- **Revenue API:** Revenue forecasting, 95% confidence bounds, churn classification, K-Means RFM clustering, revenue simulations (5 tests).
- **Decision Engine API:** Rule evaluations, evidence packaging, grounded AI explanations (1 test).
- **Approvals & Action Execution API:** Approval state machine, idempotent action dispatching (2 tests).
- **End-to-End Enterprise Scenario:** Complete end-to-end integration workflow testing (1 test).
- **Total:** **40 tests passing (100% pass rate)**.

