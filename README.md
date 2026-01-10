
---

# MetaCheck — Webpage Metadata Analyzer

MetaCheck is a lightweight web application that extracts objective metadata from online articles and webpages.  
Instead of generating credibility scores, MetaCheck surfaces structured metadata aligned with key CRAAP dimensions — **Currency**, **Authority**, and **Relevance** — helping users make informed judgments about online content.

The system consists of:

- A **FastAPI backend** that fetches webpages, extracts metadata, enriches it (e.g., DOI lookup), and returns structured JSON  
- A **minimal frontend** (HTML/CSS/JS) that sends URLs to the backend and displays the extracted metadata

---

## Features

- Extracts metadata from:
  - HTML meta tags  
  - OpenGraph & Twitter Cards  
  - Schema.org  
  - DOI (with optional DataCite enrichment)
- Normalises dates and author information
- Optional domain/IP reputation lookup
- Graceful fallback when metadata is missing
- Transparent raw JSON output
- Fully containerised backend (Docker)

---

## 📁 Project Structure

```
src/backend/craap/
├── main.py                 # FastAPI entry point
├── api/v1/
│   ├── analyzer.py         # /analyze/url endpoint
│   └── metrics.py
├── model/data_model.py     # Pydantic models
└── processing/
    └── extractor.py        # Metadata extraction pipeline

frontend/
├── main-page.html
├── about-craap.html
├── app.js
└── styles.css
```

---

## 🚀 Running MetaCheck (Without Docker)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the backend

```bash
uvicorn src.backend.craap.main:app --host 0.0.0.0 --port 10124 --reload
```

Backend will be available at:

```
http://localhost:10124
```

### 3. Open the frontend

Open the file:

```
frontend/main-page.html
```

in your browser.

---

## Running MetaCheck with Docker (Recommended)

### 1. Build & start the service

```bash
docker compose up --build
```

### 2. Access the API

```
http://localhost:10124
```

### 3. Use the frontend

Open:

```
frontend/main-page.html
```

The frontend communicates with the backend automatically.

---

## API Overview

### **POST /analyze/url**

Accepts:

- `application/x-www-form-urlencoded`
- JSON body
- Query parameter

Example:

```bash
curl -X POST -d "url=https://example.com" http://localhost:10124/analyze/url
```

Returns structured metadata:

```json
{
  "status": "success",
  "timestamp": "...",
  "raw_meta_tags": { ... },
  "confidence": 0.8
}
```

---

## Error Handling

MetaCheck is designed to degrade gracefully:

- Invalid URLs → 422 or 400  
- Network failures → safe fallback  
- Missing metadata → returned as `null`  
- External API failures (DataCite, reputation) → ignored without breaking extraction  

---

## Notes & Limitations

- Frontend is intentionally minimal (no frameworks)
- No credibility scoring — only metadata extraction
- External enrichment is optional and non-blocking
- Not intended as a production UI; backend is the core

---
