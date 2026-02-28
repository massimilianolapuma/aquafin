# 🗺️ Aquafin — Roadmap

> Roadmap pubblica delle funzionalità pianificate.
> Tracking dettagliato: [GitHub Project](https://github.com/orgs/massimilianolapuma/projects/2/views/1)
> Ultimo aggiornamento: 28 Febbraio 2026

---

## Legenda

| Stato | Significato |
|---|---|
| ✅ | Completato |
| 🚧 | In corso |
| 📋 | Pianificato |
| 💡 | In valutazione |
| ❌ | Scartato / Rimandato |

---

## Ciclo 1 — MVP Web 🚧

**Obiettivo**: App web funzionante per importare, categorizzare e analizzare transazioni bancarie, Satispay e PayPal.
**Timeline stimata**: 8-10 settimane
**Target**: Single user, multi-conto, italiano + inglese

### Infrastruttura

| Feature | Stato | Note |
|---|---|---|
| Monorepo setup (backend + frontend) | 📋 | Python + Next.js |
| Docker Compose (PostgreSQL + API + Web) | 📋 | Dev environment |
| GitHub Actions CI (lint, test, build) | 📋 | PR checks |
| Modelli dati e migrazioni DB | 📋 | Alembic + SQLAlchemy |

### Backend API

| Feature | Stato | Note |
|---|---|---|
| Autenticazione (Clerk) | 📋 | JWT, webhook sync |
| CRUD Conti (bank, Satispay, PayPal, cash) | 📋 | — |
| Upload CSV/PDF + auto-detect formato | 📋 | Multipart upload |
| Anteprima transazioni prima di conferma | 📋 | Preview endpoint |
| CRUD Transazioni + filtri avanzati | 📋 | Paginazione, search |
| Categorie predefinite + custom | 📋 | Gerarchiche, i18n |
| Regole di categorizzazione | 📋 | Keyword + regex |
| Analytics (per categoria, mese, conto) | 📋 | — |
| Export CSV/JSON | 📋 | Filtri applicabili |
| Export GDPR (dati completi utente) | 📋 | Compliance |

### Parser

| Feature | Stato | Note |
|---|---|---|
| Parser CSV generico banca italiana | 📋 | Data IT, importi con virgola |
| Parser Satispay | 📋 | Formato specifico |
| Parser PayPal | 📋 | Formato export PayPal |
| Parser PDF base (tabelle strutturate) | 📋 | pdfplumber |
| Normalizzazione dati (date, importi, descrizioni) | 📋 | Multi-formato |
| Categorizzazione automatica rule-based | 📋 | Keyword + pattern |
| Feedback "applica a simili" | 📋 | Auto-creazione regole |

### Frontend Web

| Feature | Stato | Note |
|---|---|---|
| Design System (palette, tipografia, componenti) | 📋 | Shadcn/UI + Tailwind |
| Dashboard con saldo e grafici | 📋 | Recharts |
| Pagina upload (drag & drop, anteprima) | 📋 | React Dropzone |
| Lista transazioni (filtri, inline edit) | 📋 | TanStack Table |
| Gestione categorie e regole | 📋 | — |
| Pagina analytics (torta, barre, trend) | 📋 | — |
| Gestione conti | 📋 | — |
| Export dati | 📋 | CSV/JSON download |
| i18n italiano + inglese | 📋 | next-intl |
| Responsive (mobile-first) | 📋 | — |

---

## Ciclo 2 — Intelligenza e Miglioramenti 📋

**Obiettivo**: AI per categorizzazione, budget management, UX migliorata.
**Timeline stimata**: 6-8 settimane

| Feature | Stato | Note |
|---|---|---|
| AI categorization con OpenAI GPT-4o | 📋 | Sostituisce/integra rule-based |
| PDF parser avanzato con OCR (pytesseract) | 📋 | PDF scansionati |
| PDF parser con LLM/VLM | 💡 | Per PDF non strutturati |
| Budget creation e management | 📋 | — |
| Alert overspending | 📋 | Notifiche in-app |
| Previsioni spese | 💡 | Basate su storico |
| Chat AI in-app | 📋 | Spiegazioni, insight |
| Suggerimenti risparmio personalizzati | 📋 | "30% in ristoranti" |
| Dark mode | 📋 | Tailwind dark: |
| Onboarding guidato migliorato | 📋 | Tutorial interattivo |
| Scheduled payments / pagamenti ricorrenti | 📋 | — |
| Regole avanzate matching (ML-assisted) | 💡 | — |
| Parser Revolut | 💡 | Nuovo formato |
| Parser N26 | 💡 | Nuovo formato |

---

## Ciclo 3 — Mobile 📋

**Obiettivo**: App nativa iOS e macOS con parità funzionale rispetto al web.
**Timeline stimata**: 8-12 settimane

| Feature | Stato | Note |
|---|---|---|
| App iOS (iPhone + iPad) | 📋 | SwiftUI |
| App macOS | 📋 | SwiftUI nativo |
| Shared Swift Package (modelli, API client) | 📋 | Logica condivisa |
| Dashboard mobile | 📋 | Swift Charts |
| Upload da Files / Document Picker | 📋 | — |
| Transazioni con swipe actions | 📋 | — |
| Analytics grafici nativi | 📋 | — |
| Push notifications | 📋 | Budget alerts |
| Offline mode (SwiftData cache) | 📋 | — |
| Widget iOS (saldo, spese giornaliere) | 💡 | WidgetKit |
| Apple Watch complication | 💡 | — |

---

## Ciclo 4+ — Estensioni Future 💡

| Feature | Stato | Note |
|---|---|---|
| Open Banking API (PSD2) | 💡 | Collegamento diretto banche |
| Integrazioni Plaid/Yodlee | 💡 | Aggregazione automatica |
| Investment tracking (ETF, PAC) | 💡 | Portfolio view |
| Multi-utente / famiglia | 💡 | Shared accounts |
| Fraud detection | 💡 | AI anomaly detection |
| Voice assistant | 💡 | "Quanto ho speso in ristoranti?" |
| Currency conversion multi-valuta | 💡 | API tassi cambio |
| Riconciliazione bancaria | 💡 | Match automatico |
| API pubblica per terze parti | 💡 | — |
| Self-hosted auth (Keycloak) | 💡 | Sostituisce Clerk |
| SOC 2 compliance | 💡 | Enterprise ready |
| Audit log completo | 💡 | — |
| Transaction splitting (spese condivise) | 💡 | — |
| Financial health score | 💡 | AI-driven |
| Goal tracking (obiettivi risparmio) | 💡 | — |

---

## Come contribuire alla roadmap

- **Suggerisci una feature**: apri una [GitHub Issue](https://github.com/massimilianolapuma/aquafin/issues/new) con il tag `enhancement`
- **Vota una feature**: reazioni 👍 sulle issue esistenti
- **Tracking dettagliato**: [GitHub Project Board](https://github.com/orgs/massimilianolapuma/projects/2/views/1)
