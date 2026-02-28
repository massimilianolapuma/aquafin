# 💰 Aquafin

> Applicazione di finanza personale per monitorare e classificare movimenti bancari, Satispay e PayPal.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Cos'è Aquafin?

Aquafin ti permette di:

- **Importare** estratti conto e movimenti da file CSV e PDF (banche italiane, Satispay, PayPal)
- **Categorizzare** automaticamente le transazioni con regole intelligenti
- **Analizzare** le tue spese con grafici interattivi per categoria, mese e conto
- **Esportare** i dati classificati in CSV o JSON

## Stack Tecnologico

| Layer | Tecnologia |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLAlchemy, Alembic |
| Frontend | Next.js 14+, TypeScript, Tailwind CSS, Shadcn/UI |
| Database | PostgreSQL 16 |
| Auth | Clerk |
| Deploy | Docker Compose |
| i18n | Italiano + Inglese |

## Quick Start

### Prerequisiti

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Node.js 20+](https://nodejs.org/) (per sviluppo frontend)
- [Python 3.12+](https://www.python.org/) (per sviluppo backend)
- [gh CLI](https://cli.github.com/) (opzionale, per gestione issues)

### Setup

```bash
# Clona il repository
git clone https://github.com/massimilianolapuma/aquafin.git
cd aquafin

# Copia le variabili d'ambiente
cp .env.example .env

# Avvia tutti i servizi
docker compose up -d

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Sviluppo

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Struttura Progetto

```
aquafin/
├── backend/          # FastAPI backend (Python)
├── frontend/         # Next.js frontend (TypeScript)
├── mobile/           # iOS/macOS app — Ciclo 3 (SwiftUI)
├── shared/           # Risorse condivise (categorie, config)
├── docker-compose.yml
└── .github/
    ├── PLANNING.md   # Piano architetturale completo
    └── ROADMAP.md    # Roadmap delle funzionalità
```

## Documentazione

- [📋 Piano di Progetto](.github/PLANNING.md) — Architettura, modello dati, API, design system
- [🗺️ Roadmap](.github/ROADMAP.md) — Funzionalità pianificate e stato di avanzamento
- [📌 Project Board](https://github.com/orgs/massimilianolapuma/projects/2/views/1) — Task tracking

## Roadmap

| Ciclo | Focus | Status |
|---|---|---|
| **Ciclo 1** | MVP Web — Upload, parsing, categorizzazione, analytics | 🚧 In corso |
| **Ciclo 2** | AI categorization, budget, dark mode, chat AI | 📋 Pianificato |
| **Ciclo 3** | Mobile iOS/macOS (SwiftUI) | 📋 Pianificato |
| **Ciclo 4+** | Open Banking, investment tracking, multi-utente | 💡 In valutazione |

Vedi la [Roadmap completa](.github/ROADMAP.md) per tutti i dettagli.

## Contribuire

1. Apri una [Issue](https://github.com/massimilianolapuma/aquafin/issues/new) per bug o feature request
2. Vota con 👍 le feature che vorresti vedere implementate
3. Segui il [Project Board](https://github.com/orgs/massimilianolapuma/projects/2/views/1) per lo stato di avanzamento

## Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per dettagli.
