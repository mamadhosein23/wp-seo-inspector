# WP SEO Inspector 🔍
**A Modular Technical SEO Audit Engine & Analytics Dashboard.**

WP SEO Inspector is a full-stack tool designed to perform deep-dive technical audits of web pages. It focuses on extracting critical on-page signals, validating SEO best practices, and calculating a transparent "SEO Health Score" based on a rule-driven engine.

---

## 🚀 Key Modules (Under Development)

The system is architected to be modular and extensible:

- **`http_client.py`**: Asynchronous fetching engine using `httpx` with custom User-Agent rotations and error handling for common HTTP status codes.
- **`analyzer.py`**: High-speed DOM parsing using `BeautifulSoup4` and `lxml`. Extracts metadata, heading hierarchies, link structures, and media assets.
- **`scorer.py`**: A rule-based scoring algorithm that evaluates page health. It assigns weighted penalties for missing tags, broken hierarchies, or accessibility issues.
- **`schemas.py`**: Strict data validation using `Pydantic` to ensure consistent communication between the FastAPI backend and Next.js frontend.

---

## 🛠 Tech Stack

### Backend (The Engine)
- **FastAPI**: Asynchronous Python framework for high-performance API endpoints.
- **BS4 + lxml**: Robust HTML parsing and data extraction.
- **Pydantic**: Type hinting and data serialization.

### Frontend (The Dashboard)
- **Next.js 14+**: App Router-based architecture for the analytics interface.
- **Tailwind CSS**: Responsive and minimalist UI design.
- **TypeScript**: Ensuring end-to-end type safety.

---

## 📊 Scoring Methodology

Unlike generic tools, the score here is **deductive**. Every page starts at **100 points**, and points are deducted based on severity:

| Severity | Issue Example | Penalty |
| :--- | :--- | :--- |
| 🔴 **Critical** | Missing H1 tag, Noindex meta, or 4xx/5xx status | -20 to -40 |
| 🟡 **Warning** | Title too long/short, Missing Alt tags, Missing Meta Description | -10 to -15 |
| 🔵 **Notice** | Missing OpenGraph tags, Sub-optimal heading density | -5 |

---

## 🏗 Project Structure
```text
backend/app/
├── main.py          # API Routes & Entry Point
├── http_client.py   # Page Fetching Logic
├── analyzer.py      # HTML Parsing & Extraction
├── scorer.py        # SEO Scoring Logic
├── schemas.py       # Pydantic Data Models
└── security.py      # Auth & Security Middlewares
