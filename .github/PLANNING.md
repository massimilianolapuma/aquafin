# Aquafin — Piano di Progetto

> Documento di tracking architetturale e operativo.
> Ultimo aggiornamento: 28 Febbraio 2026

---

## Indice

- [Visione](#visione)
- [Personas e Obiettivi](#personas-e-obiettivi)
- [User Stories MVP](#user-stories-mvp)
- [Feature Matrix (MVP vs Post-MVP)](#feature-matrix-mvp-vs-post-mvp)
- [Architettura](#architettura)
- [Stack Tecnologico](#stack-tecnologico)
- [Struttura Repository](#struttura-repository)
- [Modello Dati](#modello-dati)
- [API REST](#api-rest)
- [Parsing e Categorizzazione](#parsing-e-categorizzazione)
- [Frontend Web](#frontend-web)
- [Mobile (iOS/macOS)](#mobile-iosmacos)
- [Sicurezza e Privacy](#sicurezza-e-privacy)
- [UX e Flussi Utente](#ux-e-flussi-utente)
- [Organizzazione Agenti](#organizzazione-agenti)
- [Cicli di Sviluppo](#cicli-di-sviluppo)
- [Decisioni Architetturali](#decisioni-architetturali)
- [Verification](#verification)

---

## Visione

Aquafin è un'applicazione di finanza personale che importa movimenti bancari, Satispay e PayPal da CSV/PDF, li normalizza, li categorizza (rule-based nell'MVP, AI dal Ciclo 2), e fornisce dashboard analitiche. L'architettura è modulare e orientata a microservizi per consentire lavoro parallelo tra agenti AI e futura estensione a iOS/macOS (SwiftUI).

---

## Personas e Obiettivi

| Persona | Obiettivo Primario |
|---|---|
| **Single / Giovane lavoratore** | Capire dove vanno i soldi, controllare le spese ricorrenti |
| **Coppia** | Gestire spese condivise, visibilità su più conti |
| **Freelancer / P.IVA** | Separare spese personali/professionali, export per commercialista |
| **Famiglia** | Budget familiare, monitoraggio spese figli, gestione multi-conto |

---

## User Stories MVP

1. **US-001** — Come utente, voglio caricare un file CSV/PDF della mia banca, Satispay o PayPal, per importare i movimenti.
2. **US-002** — Come utente, voglio vedere un'anteprima delle transazioni estratte prima di confermarle.
3. **US-003** — Come utente, voglio che le transazioni vengano categorizzate automaticamente (rule-based).
4. **US-004** — Come utente, voglio correggere manualmente la categoria di una transazione e che il sistema "impari" la mia preferenza.
5. **US-005** — Come utente, voglio visualizzare le spese per categoria, mese e conto con grafici interattivi.
6. **US-006** — Come utente, voglio esportare i dati classificati in CSV o JSON.
7. **US-007** — Come utente, voglio gestire più conti (banca, Satispay, PayPal) in un'unica dashboard.
8. **US-008** — Come utente, voglio che l'app sia in italiano e inglese.

---

## Feature Matrix (MVP vs Post-MVP)

| MVP (Ciclo 1) | Ciclo 2 | Ciclo 3+ |
|---|---|---|
| Upload CSV/PDF | AI categorization (LLM) | Mobile iOS/macOS |
| Parsing & normalizzazione | Budget e alert overspending | Open Banking API |
| Categorie predefinite + custom | Previsioni spese | Investment tracking (ETF/PAC) |
| Dashboard con grafici | Chat AI in-app | Multi-utente (famiglia) |
| Export CSV/JSON | Regole avanzate matching | Integrazioni Plaid/Yodlee |
| Auth (Clerk) | Scheduled payments | Notifiche push |
| Multi-conto | Onboarding guidato | Fraud detection |
| i18n IT/EN | Dark mode | Voice assistant |

---

## Architettura

```
┌─────────────────────────────────────────────────────┐
│                    CLIENT LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  Next.js Web  │  │  iOS (Swift  │  │  macOS    │ │
│  │  (React/TS)   │  │   UI)        │  │ (SwiftUI) │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
└─────────┼──────────────────┼───────────────┼────────┘
          │                  │               │
          ▼                  ▼               ▼
┌─────────────────────────────────────────────────────┐
│                   API GATEWAY                        │
│              (FastAPI / REST + future GraphQL)        │
├──────────┬──────────┬──────────┬───────────┬────────┤
│  Auth    │ Accounts │ Transac- │ Categories│ Export  │
│ (Clerk)  │  Module  │  tions   │  Module   │ Module  │
├──────────┴──────────┴──────────┴───────────┴────────┤
│                  SERVICES LAYER                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐ │
│  │  Parser   │  │ Categori- │  │  Analytics       │ │
│  │  Service  │  │ zation    │  │  Service         │ │
│  │ (CSV/PDF) │  │ Engine    │  │                  │ │
│  └──────────┘  └───────────┘  └──────────────────┘ │
├─────────────────────────────────────────────────────┤
│                   DATA LAYER                         │
│         PostgreSQL (Docker) + File Storage           │
└─────────────────────────────────────────────────────┘
```

---

## Stack Tecnologico

| Layer | Tecnologia | Note |
|---|---|---|
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy (async), Alembic | RESTful API |
| **Frontend Web** | Next.js 14+ (App Router), TypeScript, Tailwind CSS, Shadcn/UI | i18n con next-intl |
| **Database** | PostgreSQL 16 (Docker) | pgcrypto per encryption |
| **Auth** | Clerk (MVP) → Keycloak (futuro) | JWT, MFA opzionale |
| **Grafici** | Recharts (web), Swift Charts (mobile) | Palette colori condivisa |
| **State Management** | Zustand (web), SwiftUI @Observable (mobile) | — |
| **Data Fetching** | TanStack Query (web), URLSession async/await (mobile) | — |
| **i18n** | next-intl (web) | IT + EN da subito |
| **AI (Ciclo 2)** | OpenAI API (GPT-4o) | Rule-based per MVP |
| **PDF Parsing** | pdfplumber, pytesseract (OCR Ciclo 2) | — |
| **CSV Parsing** | pandas | — |
| **CI/CD** | GitHub Actions | Lint + test + build |
| **Deploy** | Docker Compose | Portabile su qualsiasi cloud |
| **Mobile (Ciclo 3)** | SwiftUI, Swift 6, SwiftData | iOS + macOS |

---

## Struttura Repository

```
aquafin/
├── .github/
│   ├── copilot-instructions.md
│   ├── PLANNING.md             # Questo documento
│   ├── ROADMAP.md              # Roadmap pubblica
│   └── workflows/              # GitHub Actions CI/CD
│       ├── backend-ci.yml
│       └── frontend-ci.yml
├── backend/
│   ├── app/
│   │   ├── api/v1/             # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── accounts.py
│   │   │   ├── transactions.py
│   │   │   ├── categories.py
│   │   │   └── exports.py
│   │   ├── core/               # Config, security, deps
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   └── category.py
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/
│   │   │   ├── parser/
│   │   │   │   ├── base.py          # BaseParser protocol
│   │   │   │   ├── csv_parser.py
│   │   │   │   ├── pdf_parser.py
│   │   │   │   ├── bank_parser.py
│   │   │   │   ├── satispay_parser.py
│   │   │   │   └── paypal_parser.py
│   │   │   ├── categorization/
│   │   │   │   ├── engine.py
│   │   │   │   ├── rules.py
│   │   │   │   └── ai_categorizer.py  # Ciclo 2
│   │   │   └── analytics/
│   │   │       └── service.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── migrations/     # Alembic
│   │   └── main.py
│   ├── tests/
│   │   ├── fixtures/           # File CSV/PDF di test
│   │   ├── test_parsers/
│   │   ├── test_categorization/
│   │   └── test_api/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── app/[locale]/       # Next.js App Router + i18n
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Dashboard
│   │   │   ├── upload/page.tsx
│   │   │   ├── transactions/page.tsx
│   │   │   ├── categories/page.tsx
│   │   │   ├── analytics/page.tsx
│   │   │   ├── accounts/page.tsx
│   │   │   └── export/page.tsx
│   │   ├── components/
│   │   │   ├── ui/             # Shadcn/UI
│   │   │   ├── charts/
│   │   │   ├── upload/
│   │   │   └── transactions/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── utils.ts
│   │   │   └── i18n.ts
│   │   ├── hooks/
│   │   ├── stores/             # Zustand
│   │   └── messages/
│   │       ├── it.json
│   │       └── en.json
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── package.json
│   └── Dockerfile
├── mobile/                     # Ciclo 3
│   └── aquafin-ios/
├── shared/
│   └── categories.json         # Categorie predefinite
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── README.md
```

---

## Modello Dati

### users

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PK | — |
| `clerk_id` | VARCHAR UNIQUE | External ID da Clerk |
| `email` | VARCHAR UNIQUE | — |
| `display_name` | VARCHAR | — |
| `locale` | VARCHAR(5) | Default: 'it' |
| `preferences` | JSONB | Valuta default, tema, ecc. |
| `created_at` | TIMESTAMP | — |
| `updated_at` | TIMESTAMP | — |

### accounts

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PK | — |
| `user_id` | UUID FK → users | — |
| `name` | VARCHAR | Es: "Conto BNL", "Satispay" |
| `type` | ENUM | bank, satispay, paypal, cash, other |
| `currency` | VARCHAR(3) | ISO 4217, default EUR |
| `color` | VARCHAR(7) | Hex color per UI |
| `icon` | VARCHAR | Nome icona |
| `is_active` | BOOLEAN | Default true |
| `created_at` | TIMESTAMP | — |

### categories

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PK | — |
| `user_id` | UUID FK nullable | NULL = categoria di sistema |
| `parent_id` | UUID FK self nullable | Per gerarchia |
| `name_key` | VARCHAR | Chiave i18n (es: "cat.food") |
| `name_custom` | VARCHAR nullable | Nome custom utente |
| `icon` | VARCHAR | — |
| `color` | VARCHAR(7) | — |
| `is_system` | BOOLEAN | Non eliminabile |
| `is_income` | BOOLEAN | true = entrata, false = uscita |
| `sort_order` | INTEGER | — |

### transactions

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PK | — |
| `account_id` | UUID FK → accounts | — |
| `category_id` | UUID FK → categories nullable | — |
| `import_id` | UUID FK → imports nullable | NULL se manuale |
| `amount` | DECIMAL(12,2) | Positivo = entrata, negativo = uscita |
| `currency` | VARCHAR(3) | — |
| `date` | DATE | Data operazione |
| `description` | VARCHAR | Descrizione normalizzata |
| `original_description` | VARCHAR | Descrizione originale dal file |
| `type` | ENUM | income, expense, transfer |
| `categorization_method` | ENUM | auto, manual, rule |
| `is_recurring` | BOOLEAN | — |
| `tags` | JSONB | Tag liberi |
| `metadata` | JSONB | Dati extra source-specific |
| `created_at` | TIMESTAMP | — |
| `updated_at` | TIMESTAMP | — |

### imports

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PK | — |
| `account_id` | UUID FK → accounts | — |
| `user_id` | UUID FK → users | — |
| `filename` | VARCHAR | Nome file originale |
| `file_type` | ENUM | csv, pdf |
| `source_type` | ENUM | bank, satispay, paypal, other |
| `status` | ENUM | pending, processing, completed, failed |
| `row_count` | INTEGER | Righe processate |
| `imported_count` | INTEGER | Righe importate |
| `error_log` | JSONB | Errori di parsing |
| `created_at` | TIMESTAMP | — |

### categorization_rules

| Campo | Tipo | Note |
|---|---|---|
| `id` | UUID PK | — |
| `user_id` | UUID FK → users | — |
| `category_id` | UUID FK → categories | — |
| `pattern` | VARCHAR | Keyword o regex |
| `match_type` | ENUM | contains, regex, exact |
| `priority` | INTEGER | Regole utente > sistema |
| `is_active` | BOOLEAN | — |
| `created_at` | TIMESTAMP | — |

### Categorie Predefinite

**Spese:**
- 🛒 Alimentari
- 🍽️ Ristoranti e Bar
- 🚗 Trasporti → ⛽ Carburante, 🚌 Trasporto pubblico, 🚕 Taxi/Ride sharing
- 🏠 Abitazione → 🏡 Affitto/Mutuo, 💡 Utenze, 🔧 Manutenzione
- 💊 Salute e Benessere
- 👕 Abbigliamento
- 🎬 Svago e Intrattenimento
- ✈️ Viaggi e Vacanze
- 📱 Abbonamenti e Servizi digitali
- 📚 Istruzione e Formazione
- 🎁 Regali
- 🐾 Animali domestici
- 🏛️ Tasse e Imposte
- 💳 Commissioni bancarie
- ❓ Altro / Da classificare

**Entrate:**
- 💰 Stipendio
- 💼 Freelance / Lavoro autonomo
- 📈 Investimenti e Rendite
- 🔄 Rimborsi
- 🎁 Regali ricevuti
- ❓ Altro

---

## API REST

Base URL: `/api/v1`

### Auth

| Metodo | Endpoint | Descrizione |
|---|---|---|
| POST | `/auth/webhook` | Clerk webhook per sync utente |
| GET | `/users/me` | Profilo utente corrente |
| PUT | `/users/me` | Aggiorna profilo |
| DELETE | `/users/me` | Cancella account e dati (GDPR) |

### Accounts

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/accounts` | Lista conti |
| POST | `/accounts` | Crea conto |
| GET | `/accounts/{id}` | Dettaglio conto |
| PUT | `/accounts/{id}` | Modifica conto |
| DELETE | `/accounts/{id}` | Elimina conto (soft delete) |

### Imports

| Metodo | Endpoint | Descrizione |
|---|---|---|
| POST | `/imports/upload` | Upload file CSV/PDF (multipart) |
| GET | `/imports` | Lista import |
| GET | `/imports/{id}` | Dettaglio import |
| GET | `/imports/{id}/preview` | Anteprima transazioni estratte |
| POST | `/imports/{id}/confirm` | Conferma import |
| DELETE | `/imports/{id}` | Annulla import |

### Transactions

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/transactions` | Lista (filtri: account_id, category_id, date_from, date_to, type, search, page, limit) |
| GET | `/transactions/{id}` | Dettaglio |
| PUT | `/transactions/{id}` | Modifica (categoria, tags, description) |
| POST | `/transactions/{id}/recategorize` | Ri-categorizza + flag "applica a simili" |
| DELETE | `/transactions/{id}` | Elimina |
| POST | `/transactions/bulk-categorize` | Categorizzazione di massa |

### Categories

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/categories` | Lista (sistema + custom) |
| POST | `/categories` | Crea custom |
| PUT | `/categories/{id}` | Modifica |
| DELETE | `/categories/{id}` | Elimina (solo custom) |
| GET | `/categories/rules` | Lista regole |
| POST | `/categories/rules` | Crea regola |
| PUT | `/categories/rules/{id}` | Modifica regola |
| DELETE | `/categories/rules/{id}` | Elimina regola |

### Analytics

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/analytics/summary?period=month` | Totali income/expense/balance |
| GET | `/analytics/by-category?date_from&date_to` | Breakdown per categoria |
| GET | `/analytics/by-month?months=12` | Trend mensile |
| GET | `/analytics/by-account?date_from&date_to` | Breakdown per conto |

### Export

| Metodo | Endpoint | Descrizione |
|---|---|---|
| GET | `/exports/csv?filters...` | Export CSV filtrato |
| GET | `/exports/json?filters...` | Export JSON filtrato |
| GET | `/exports/gdpr` | Export completo dati utente (GDPR) |

---

## Parsing e Categorizzazione

### Flusso

```
Upload File → Detect Type (CSV/PDF) → Detect Source (Bank/Satispay/PayPal)
    │
    ▼
Parse (source-specific parser) → Normalize → Categorize (rule-based) → Preview
    │
    ▼
User Review → Confirm/Edit → Save to DB + Update Rules
```

### Parser Architecture

`BaseParser` protocol con metodi:
- `detect(file) → bool` — identifica se il file è compatibile con questo parser
- `parse(file) → list[RawTransaction]` — estrae le transazioni
- `get_column_mapping() → dict` — restituisce il mapping colonne

Parser specifici:
- **BankCSVParser**: colonne italiane (Data, Valuta, Descrizione, Dare/Avere), formati data IT, importi con virgola
- **SatispayParser**: formato Satispay (ID, Data, Tipo, Importo, Valuta, Nome, Descrizione)
- **PayPalParser**: formato PayPal (Date, Name, Type, Currency, Gross, Fee, Net)
- **PDFParser**: estrazione tabelle con `pdfplumber`, OCR con `pytesseract` (Ciclo 2)

### Normalizzazione

| Campo | Regole |
|---|---|
| Data | Multi-formato (`dd/mm/yyyy`, `yyyy-mm-dd`, `mm/dd/yyyy`) → `date` (UTC) |
| Importo | Rimozione simboli, virgola/punto → `Decimal`. Negativi = uscite |
| Descrizione | Trim, preserva originale in `original_description` |
| Valuta | Default EUR, codice ISO 4217 |
| Tipo | Inferito da segno importo |

### Categorizzazione Rule-Based (MVP)

1. **User rules** (priorità massima): regole personalizzate dall'utente
2. **Keyword matching**: dizionario keywords → categoria
3. **Pattern matching**: regex per pattern ricorrenti
4. **Fallback**: "Da classificare"

### Feedback Loop

- Utente ri-categorizza → opzione "Applica a simili" → crea `categorization_rule` automatica
- Regole utente sovrascrivono regole di sistema

---

## Frontend Web

### Design System

| Elemento | Specifica |
|---|---|
| Palette primaria | Blu-teal `#0EA5E9` |
| Success / Income | Verde `#22C55E` |
| Danger / Expense | Rosso `#EF4444` |
| Warning | Amber `#F59E0B` |
| Neutral | Slate scale |
| Background | White / Slate-50 |
| Tipografia body | Inter |
| Tipografia numeri | JetBrains Mono |
| Border radius | 8px cards, 6px inputs, 16px large |
| Spacing | 4px grid (Tailwind) |
| Icone | Lucide Icons |
| Dark mode | Predisposto, implementazione Ciclo 2 |
| Responsive | Mobile-first: sm(640), md(768), lg(1024), xl(1280) |

### Schermate

1. **Dashboard** — Saldo totale, spese/entrate mese, torta categorie, trend 6 mesi, ultime 10 transazioni
2. **Upload** — Drag & drop, selezione sorgente, selezione conto, progress, anteprima tabella, conferma
3. **Transazioni** — Tabella paginata + filtri, inline edit categoria, bulk actions, raggruppamento per data
4. **Categorie** — Lista con spesa totale, gestione custom, regole matching
5. **Analytics** — Torta per categoria, barre per mese, stacked bar per conto, line trend, filtri temporali, comparazione
6. **Conti** — Lista conti con info, cronologia import
7. **Export** — Filtri → download CSV/JSON

---

## Mobile (iOS/macOS) — Ciclo 3

- SwiftUI + MVVM, shared business logic via Swift Package
- URLSession async/await, SwiftData per cache offline
- Clerk SDK iOS, Swift Charts
- Stessi colori (Color extension), SF Symbols (equivalenti Lucide)

| Schermata | iOS | macOS |
|---|---|---|
| Dashboard | Tab bar, card verticale | Sidebar, dashboard ampia |
| Upload | Sheet modale, document picker | Drag & drop, file picker |
| Transazioni | Lista + swipe actions | Tabella con colonne sortabili |
| Analytics | Grafici scrollabili, full width | Grafici affiancati |

---

## Sicurezza e Privacy

| Area | Implementazione |
|---|---|
| Auth | Clerk (MFA, session management, JWT) |
| HTTPS | TLS 1.3 obbligatorio |
| Encryption at rest | PostgreSQL pgcrypto |
| File handling | Processing in memoria, eliminazione dopo 24h max |
| API Security | Rate limiting (slowapi), CORS, Pydantic validation, SQLAlchemy ORM |
| GDPR | Consenso esplicito, export completo, cancellazione dati, no PII nei log |
| Data isolation | Ogni query filtrata per user_id |
| Secrets | .env dev, Docker secrets / vault prod |

---

## UX e Flussi Utente

### Onboarding

Welcome → 3 step (Upload → Categorizza → Analizza) → Crea primo conto → "Carica il tuo primo estratto conto"

### Upload Flow

Drag & drop → auto-detect formato → parsing → anteprima (✓ verde / ⚠ giallo / ✗ rosso per confidence) → modifica/conferma → summary

### Correzione Categorie

Click categoria → dropdown con search → selezione → checkbox "Applica a simili" → feedback visivo

### AI Conversazionale (Ciclo 2)

Chat panel: spiegazione categorizzazione, suggerimenti spesa, insight personalizzati

---

## Organizzazione Agenti

| Agente | Directory | Indipendenza |
|---|---|---|
| Backend | `backend/` | Autonomo (API contract) |
| Frontend Web | `frontend/` | Dipende da API contract |
| Parsing/AI | `backend/app/services/parser/`, `categorization/` | Autonomo (BaseParser interface) |
| Mobile | `mobile/` | Dipende da API contract (Ciclo 3) |
| DevSecOps | `.github/workflows/`, Docker configs | Autonomo |
| Sicurezza | Trasversale | Review su tutti |

**Contratto API**: `backend/openapi.yaml` (auto-generato da FastAPI) come single source of truth.

---

## Cicli di Sviluppo

### Ciclo 1 — MVP Web (8-10 settimane)

| Step | Attività | Agente | Status |
|---|---|---|---|
| 1.1 | Setup monorepo, Docker Compose, CI base | DevSecOps | ⬜ |
| 1.2 | Modelli dati, migrazioni Alembic, seed categorie | Backend | ⬜ |
| 1.3 | API auth (Clerk) + CRUD accounts | Backend | ⬜ |
| 1.4 | Parser CSV (bank + Satispay + PayPal) | Parsing | ⬜ |
| 1.5 | API upload + preview + confirm + categorizzazione | Backend + Parsing | ⬜ |
| 1.6 | API transactions + analytics + export | Backend | ⬜ |
| 1.7 | Setup Next.js + Tailwind + Shadcn + i18n + Clerk | Frontend | ⬜ |
| 1.8 | Dashboard + upload flow + transactions list | Frontend | ⬜ |
| 1.9 | Analytics charts + export + categorie | Frontend | ⬜ |
| 1.10 | Testing E2E, security review, docs | Tutti | ⬜ |

### Ciclo 2 — Miglioramenti (6-8 settimane)

AI categorization, PDF avanzato, Budget, Dark mode, Chat AI, Scheduled payments

### Ciclo 3 — Mobile (8-12 settimane)

iOS app, macOS app, Shared Swift Package, Push notifications, Offline mode

---

## Decisioni Architetturali

| # | Decisione | Motivazione |
|---|---|---|
| ADR-001 | Python/FastAPI per backend | Ecosistema parsing PDF/CSV, futuro AI/ML |
| ADR-002 | PostgreSQL da subito | Evita migrazione, JSONB per metadata |
| ADR-003 | Clerk per auth MVP | Setup rapido, migrazione Keycloak pianificata |
| ADR-004 | Rule-based categorization MVP | Semplicità, AI dal Ciclo 2 |
| ADR-005 | Multilingua da subito (IT/EN) | next-intl con routing locale |
| ADR-006 | Docker Compose deploy | Portabile, indipendente da cloud provider |
| ADR-007 | Monorepo | Un repo per tutto, coordinamento semplice |
| ADR-008 | Categorie gerarchiche | Flessibilità senza over-engineering |
| ADR-009 | Next.js App Router | SSR, routing, i18n nativo |
| ADR-010 | File non persistiti | Privacy: processing in memoria, delete dopo parsing |

---

## Verification

- **Backend**: `pytest` coverage ≥80%, test parser con file fixture per ogni sorgente
- **Frontend**: `vitest` + `@testing-library/react`, Playwright E2E
- **Integration**: Docker Compose up → upload → parsing → dashboard
- **Security**: `bandit` (SAST Python), `npm audit`, headers check
- **CI**: GitHub Actions → lint + test + build su ogni PR
