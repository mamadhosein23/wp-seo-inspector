# 🔍 WP SEO Inspector
**A High-Performance Technical SEO Audit Engine & Analytics Interface.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Language-Python%203.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

WP SEO Inspector is a specialized auditing engine designed to dissect web pages and evaluate their technical SEO health. By combining a robust Python-based crawler with a rule-driven scoring system, it provides developers and SEO specialists with actionable insights into page architecture, metadata integrity, and social signals.

---

## 🏗 Modular System Architecture

The project follows a strict **Separation of Concerns (SoC)** to ensure maintainability and speed:

- **Fetcher (`http_client.py`)**: Asynchronous HTTP client utilizing `httpx`. Handles redirects, custom User-Agents, and connection timeouts to mimic real-world crawling scenarios.
- **Parser (`analyzer.py`)**: Leveraging `BeautifulSoup4` with the `lxml` engine for sub-millisecond DOM traversal. It extracts over 20+ SEO signals.
- **Engine (`scorer.py`)**: The brain of the project. It runs a weighted heuristic algorithm to transform raw HTML data into a standardized health score (0-100).
- **Interface (`Next.js Dashboard`)**: A reactive dashboard that visualizes data points through SVG gauges and severity-sorted issue cards.

---

## 📊 The Scoring Algorithm (Logic-First)

The audit isn't just a checklist; it's a **Deductive Weighting System**. We start at **100** and deduct based on technical impact:

| Metric Group | Key Indicators | Max Impact |
| :--- | :--- | :--- |
| **Indexability** | Robots Meta, Canonical Tags, Status Codes | `-40 pts` |
| **Structure** | H1-H6 Hierarchy, Single H1 Enforcement | `-20 pts` |
| **Metadata** | Title & Description Length/Presence | `-25 pts` |
| **Accessibility** | Image Alt Text coverage, Link Descriptors | `-15 pts` |
| **Social Graph** | OpenGraph (OG) and Twitter Card tags | `-10 pts` |

---

## 🛠 Tech Stack

- **Backend:** FastAPI (Async/Await), Pydantic v2, BeautifulSoup4, LXML.
- **Frontend:** Next.js 14 (App Router), Tailwind CSS, TypeScript, Recharts.
- **API Design:** RESTful principles with JSON-Schema validation.

---

## 📂 Repository Structure
```text
├── backend/app/
│   ├── main.py          # FastAPI Entry Point & Routing
│   ├── analyzer.py      # DOM Extraction Logic
│   ├── scorer.py        # Rule-based Scoring Engine
│   ├── http_client.py   # Async Web Fetching
│   └── schemas.py       # Pydantic Models for Type Safety
└── frontend/src/
├── app/             # Next.js Pages & Layouts
├── components/      # UI Elements (AuditDashboard, UrlForm)
└── lib/             # API Fetching & Utility functions





