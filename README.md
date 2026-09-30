# PackSage AI (PackWise AI)

> **Ministry of Food Processing Industries (MoFPI) — Problem Statement 26236**  
> **AI-Based Intelligent Food Packaging Material Recommendation System for Food Commodities**

PackSage AI is an intelligent, full-stack decision-support system designed to optimize food packaging material selection. It balances shelf life, food preservation risks, mechanical barrier constraints, economic viability, and environmental sustainability.

---

## 1. System Architecture

The application is structured as a decoupled client-server architecture:
- **Frontend:** React 18, TypeScript 5.8, Vite, Tailwind CSS v4, Lucide Icons, and TanStack Query.
- **Backend API:** FastAPI (Python 3.10+ / 3.13), Pydantic v2, SQLAlchemy ORM (SQLite / PostgreSQL), Argon2id & JWT Authentication.
- **Recommendation Engine:** Deterministic Food Science Rule Engine (`rule_engine.py`) combined with a Scikit-Learn `RandomForestRegressor` ML scoring pipeline (`ml_engine.py`).
- **Generative AI Layer:** Optional Google Gemini integration (`gemini_service.py`) for technical rationale generation with a deterministic heuristic fallback.
- **Reporting & Verification:** ReportLab PDF generator and dynamic QR code verification.

```
                              ┌────────────────────────────────────────┐
                              │           Frontend (Vite/React)        │
                              │  Tailwind CSS v4 + Lucide + i18n       │
                              │  TanStack Query + Axios Client         │
                              └──────────────────┬─────────────────────┘
                                                 │ HTTP / REST
                                                 ▼
                              ┌────────────────────────────────────────┐
                              │          FastAPI Backend Engine        │
                              │      CORS, Pydantic, Argon2id, JWT     │
                              └───────┬──────────────┬───────────────┬─┘
                                      │              │               │
            ┌─────────────────────────┴────┐   ┌─────┴──────┐   ┌────┴──────────────────────────┐
            ▼                              ▼   ▼            ▼   ▼                               ▼
┌──────────────────────┐        ┌───────────────────┐ ┌───────────────────┐        ┌──────────────────┐
│ SQLite / PostgreSQL  │        │   Rule Engine     │ │   Scikit-Learn    │        │  Google Gemini   │
│ SQLAlchemy 2.0 ORM   │        │ Deterministic OTR │ │  Random Forest    │        │ Generative AI    │
│ Users, Scenarios,    │        │ WVTR, Temperature │ │  Empirical Fit    │        │ Engineering      │
│ Materials, Audits    │        │ & Barrier Rules   │ │  Scoring Engine   │        │ Rationale Gen    │
└──────────────────────┘        └───────────────────┘ └───────────────────┘        └──────────────────┘
                                                 │
                                                 ▼
                                ┌───────────────────────────────────┐
                                │     ReportLab & QR Generator      │
                                │   Downloadable PDF & QR Trace     │
                                └───────────────────────────────────┘
```

---

## 2. Key Features

1. **Authentication & RBAC:**
   - Argon2id password hashing and JWT access tokens.
   - Distinct roles: `admin`, `engineer`, `field_user`.
   - Protected routes and session persistence on browser reload.
2. **Packaging Recommendation Workflow:**
   - 4-step wizard with built-in commodity presets (Potato Chips, Fresh Tomatoes, Basmati Rice, Frozen Peas).
   - Validation for moisture, fat/oil, pH, respiration rate, storage conditions, transit days, target shelf life, and commercial parameters.
3. **Packaging Cost Estimation & Optimization Engine (`cost_engine.py`):**
   - **Unit-Safe Mass Calculation:** $\text{Mass } (g) = \text{Area } (cm^2) \times \text{Thickness } (cm) \times \text{Density } (g/cm^3)$.
   - **Itemized Bill of Materials:** Raw polymer resin + scrap wastage ($5\%-8\%$) + converting + heat sealing + printing + closures + freight.
   - **Economic Metrics:** Unit cost per package, cost per kg food, total batch production cost.
   - **4 Strategic Pareto Picks:** Best Performance, Lowest Cost, Most Sustainable, Balanced Value.
   - **Multi-Attribute Priorities:** Configurable weighting (Balanced, Lowest Cost First, Best Performance, Most Sustainable).
   - **Budget Variance Warning:** Alerts user if calculated packaging exceeds target budget.
4. **Deterministic Food Science Rules:**
   - **Lipid Oxidation Risk:** Oily foods ($\ge 15\%$ fat) enforce strict oxygen barriers ($\text{OTR} \le 5\ \text{cc/m}^2/\text{day}$) and light shielding.
   - **Moisture Sensitivity:** Low moisture products enforce tight WVTR floors to prevent caking; high relative humidity dynamically tightens barrier thresholds.
   - **Respiration & Fresh Produce:** High-respiration fresh produce rejects airtight films and enforces breathable / micro-perforated film (MAP).
   - **Cold-Crack Resistance:** Frozen storage requires materials rated to $-25^\circ\text{C}$ and enforces a $50\ \mu\text{m}$ thickness floor.
5. **Inverse Barrier Solver (USP):**
   - Given desired shelf life (e.g. 6 months in Indore), calculates numerical OTR and WVTR barrier thresholds directly.
6. **Traceable PDF & QR Reports:**
   - Vector PDF generation with ReportLab including Section 5 Packaging Cost Summary and dynamic QR code verification.
7. **Material Knowledge Base:**
   - 27 realistic commercial materials with authentic densities, scrap benchmarks, and commercial converter prices.

---

## 3. Quickstart & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm

### Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python migrate_db.py
python seed.py
uvicorn app.main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 4. Test Credentials

| Email | Password | Role |
| :--- | :--- | :--- |
| `admin@packsage.ai` | `Admin@123` | Administrator |
| `engineer@packsage.ai` | `Eng@1234` | Packaging Engineer |
| `field@packsage.ai` | `Field@12` | Field User |

---

## 5. Automated Testing

### Run All 25 Backend Tests
```powershell
cd backend
.\venv\Scripts\python -m pytest -v
```

### Run Frontend Production Build
```powershell
cd frontend
npm run build
```
cd backend
.\venv\Scripts\python.exe -m pytest tests -v
```
All 12 automated unit and integration tests covering the Rule Engine, ML Model, Packaging Science Rules, and API Endpoints pass with 100% success rate.

### Run Frontend Build Verification
```powershell
cd frontend
npm run build
```
Type checks and client bundles compile cleanly without errors.
