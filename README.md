# 🔍 WP SEO Inspector

> **Production-ready, High-Performance Technical SEO Audit Engine & Analytics Dashboard for WordPress and Web Pages.**

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Language-Python%203.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwindcss)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup (FastAPI)](#1-backend-setup-fastapi)
  - [2. Frontend Setup (Next.js)](#2-frontend-setup-nextjs)
- [API Reference](#-api-reference)
- [SEO Scoring Methodology](#-seo-scoring-methodology)
- [Roadmap](#-roadmap)
- [License & Author](#-license--author)

---

## 🌐 Overview

**WP SEO Inspector** is a full-stack technical SEO auditing platform designed to instantly crawl, parse, and evaluate web pages—with a dedicated focus on WordPress metadata patterns. It extracts critical technical signals, measures structural integrity, scores page optimization using a standardized rule engine, and presents actionable recommendations inside a modern SaaS-like analytics dashboard.

---

## ✨ Key Features

- ⚡ **Instant HTML Parsing & Inspection:** High-speed DOM parsing using Python's `lxml` and `BeautifulSoup4`.
- 📊 **Dynamic SEO Scoring Algorithm:** Deductive scoring system (0–100 scale) based on structural warnings and critical technical errors.
- 🏷️ **Comprehensive On-Page Signal Inspection:**
  - **Meta Tags:** Title tag length validation (30–60 chars), Meta Description length (70–160 chars), Robots Meta (`noindex`, `nofollow`), Canonical URL matching.
  - **Content & Structure:** Heading hierarchy analysis (Single H1 enforcement, H2 density, Word count metrics).
  - **Media & Assets:** Image inventory and Alt tag accessibility coverage.
  - **Link Architecture:** Classification and separation of Internal vs. External outbound links using TLD parsing.
  - **Structured Data & Social Graphs:** Detection of Open Graph (`og:*`) protocols and JSON-LD Schema structures.
- 📈 **Interactive Visual Analytics:** Integrated SVG Score Ring, Recharts distribution charts, and severity-sorted checklist cards.
- 🎨 **Modern SaaS UI:** Responsive, dark-mode ready interface built with Next.js App Router and Tailwind CSS.

---

## 🏗️ System Architecture
```txt
┌─────────────────────────────────────────────────────────────────┐
│                    Client Browser (Next.js)                     │
└────────────────────────────────┬────────────────────────────────┘
│
HTTP POST /api/audit { url }
│
▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend Engine                     │
│                                                                 │
│  ┌───────────────────┐    ┌────────────────┐    ┌────────────┐  │
│  │ HTTP Fetcher      │───►│ DOM Parser     │───►│ Audit      │  │
│  │ (User-Agent/Time) │    │ (BS4 + lxml)   │    │ Engine     │  │
│  └───────────────────┘    └────────────────┘    └─────┬──────┘  │
│                                                       │         │
│                                                 Scoring Rules   │
│                                                       ▼         │
│  ┌───────────────────┐                          ┌────────────┐  │
│  │ JSON Serializer   │◄─────────────────────────│ Scoring    │  │
│  │ (Pydantic Models) │                          │ Engine     │  │
│  └───────────────────┘                          └────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
│
AuditResponse JSON Payload
│
▼
┌─────────────────────────────────────────────────────────────────┐
│                Next.js Visual Analytics Dashboard               │
│      (Recharts + SVG Score Gauge + Actionable Issue Cards)       │
└─────────────────────────────────────────────────────────────────┘
