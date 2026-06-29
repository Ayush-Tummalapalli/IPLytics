# 🏏 IPLytics — AI-Powered IPL Analytics Platform

An intelligent cricket analytics platform that combines **data engineering**, **interactive visualizations**, and **AI-powered insights** to deliver deep analysis of the Indian Premier League (2008–2025).

---

## 🚀 Features

- **Player Analytics** — Runs, averages, strike rates, milestones, and season trends
- **Team Analytics** — Win/loss records, win percentages, and head-to-head comparisons
- **Venue Analytics** — Scoring patterns, chase success rates, and ground-specific insights
- **Player & Team Comparisons** — Side-by-side interactive comparisons
- **Interactive Visualizations** — Rich Plotly charts for every metric
- **AI Assistant** — Ask natural language questions, powered by Google Gemini

---

## 🛠️ Tech Stack

| Layer           | Technology                     |
|-----------------|--------------------------------|
| **Backend**     | Python, FastAPI, SQLAlchemy    |
| **Database**    | PostgreSQL                     |
| **Data**        | Pandas                         |
| **Frontend**    | Streamlit                      |
| **Viz**         | Plotly                         |
| **AI**          | Google Gemini API              |
| **Deployment**  | Render, Streamlit Cloud, Neon  |

---

## 📁 Project Structure

```
IPLytics/
│
├── backend/
│   └── app/
│       ├── routes/          # API endpoint definitions
│       ├── services/        # Business logic layer
│       ├── models/          # SQLAlchemy ORM models
│       ├── database/        # DB connection & session management
│       ├── analytics/       # Core analytics functions
│       ├── ai/              # Gemini AI integration
│       ├── config.py        # Centralized configuration
│       └── main.py          # FastAPI application entry point
│
├── frontend/
│   ├── pages/               # Streamlit multi-page app pages
│   ├── components/          # Reusable UI components
│   └── app.py               # Streamlit entry point
│
├── data/
│   ├── raw/                 # Original Kaggle CSV files
│   └── processed/           # Cleaned/transformed data
│
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL (local or [Neon](https://neon.tech))
- [Google Gemini API key](https://aistudio.google.com/app/apikey)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/IPLytics.git
cd IPLytics
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database URL and Gemini API key
```

### 5. Start the Backend

```bash
uvicorn backend.app.main:app --reload
```

Visit: [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation.

### 6. Start the Frontend

```bash
streamlit run frontend/app.py
```

Visit: [http://localhost:8501](http://localhost:8501)

---

## 📊 Dataset

This project uses the [Kaggle IPL Dataset](https://www.kaggle.com/datasets) containing:

- `matches.csv` — Match-level data (2008–2025)
- `deliveries.csv` — Ball-by-ball delivery data

Place these files in `data/raw/` before running the data ingestion pipeline.

---

## 🗺️ Development Roadmap

| Phase | Description              | Status  |
|-------|--------------------------|---------|
| 1     | Project Setup            | ✅ Done  |
| 2     | Database Design          | ✅ Done  |
| 3     | Data Ingestion Pipeline  | ✅ Done  |
| 4     | Analytics Engine         | ✅ Done  |
| 5     | FastAPI Backend          | ✅ Done  |
| 6     | Streamlit Frontend       | ✅ Done  |
| 7     | Plotly Visualizations    | ✅ Done  |
| 8     | AI Assistant (Gemini)    | ✅ Done  |
| 9     | Deployment & Docker      | ✅ Done  |

---

## 🐳 Local Containerization (Docker Compose)

You can run the entire platform locally with a single command using Docker.

### 1. Build and Start the Containers

Make sure you have your `.env` configured (especially `GEMINI_API_KEY`). Then run:

```bash
docker compose up --build -d
```

This starts:
- **Database (db)**: PostgreSQL database container mapping port `5432`
- **Backend (backend)**: FastAPI REST API container mapping port `8000`
- **Frontend (frontend)**: Streamlit container mapping port `8501`

### 2. Initialize Database & Run Ingestion inside Container

Once containers are active, run database creation and ETL script inside the backend container:

```bash
# Create database schema
docker exec -it iplytics_backend python -m backend.app.database.create_db

# Run data ingestion pipeline
docker exec -it iplytics_backend python -m backend.app.database.ingest
```

Then visit **http://localhost:8501** in your browser.

---

## ☁️ Cloud Deployment Guide

Follow these steps to deploy the production build to the cloud:

### 1. Database Setup: Neon (Serverless PostgreSQL)
1. Register for a free account at [Neon.tech](https://neon.tech).
2. Create a new project and select the PostgreSQL version.
3. Retrieve your connection string (e.g., `postgresql://user:pass@ep-hostname.us-east-2.aws.neon.tech/neondb?sslmode=require`).
4. Keep this connection string ready to configure environment variables.

### 2. Backend Deployment: Render (FastAPI Web Service)
1. Connect your GitHub repository to [Render](https://render.com).
2. Create a new **Web Service**:
   - **Environment**: `Docker`
   - **Dockerfile Path**: `backend.Dockerfile`
   - **Docker Build Context**: `.`
3. Set the following **Environment Variables**:
   - `DATABASE_URL` = (Your Neon PostgreSQL connection string)
   - `GEMINI_API_KEY` = (Your Google Gemini API key)
   - `DEBUG` = `false`
4. Once deployed, note down your backend URL (e.g., `https://iplytics-backend.onrender.com`).
5. Open Render's Shell or run locally to migrate the database:
   `python -m backend.app.database.create_db` and `python -m backend.app.database.ingest`.

### 3. Frontend Deployment: Streamlit Cloud or Render
#### Option A: Streamlit Community Cloud (Recommended)
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in.
2. Select **Deploy an app** and choose your GitHub repo.
3. Set **Main file path** to `frontend/app.py`.
4. In Advanced Settings, add the following **Secret** (or Environment Variable):
   - `BACKEND_URL` = (Your Render backend URL)
5. Deploy. Streamlit Cloud handles scaling automatically.

#### Option B: Render (Web Service)
1. Create a new **Web Service** on Render.
2. **Environment**: `Docker`, **Dockerfile Path**: `frontend.Dockerfile`.
3. Set **Environment Variables**:
   - `BACKEND_URL` = (Your Render backend URL)
4. Deploy.

---

## 📄 License

This project is for educational and portfolio purposes.

---

## 👤 Author

Built by **Ayush** as a portfolio project for AI/ML and Software Engineering internship applications.

