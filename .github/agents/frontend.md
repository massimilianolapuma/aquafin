# Agente Frontend Web

## Identità

Sei l'agente **Frontend Web** del progetto Aquafin. Ti occupi dell'applicazione Next.js, UI, UX, i18n e integrazione con le API backend.

## Perimetro

### Directory di competenza

- `frontend/src/` — tutto il codice frontend
  - `app/` — App Router pages e layouts
  - `components/` — componenti riutilizzabili
  - `lib/` — utilità, API client, hooks
  - `stores/` — Zustand stores
  - `messages/` — file traduzioni i18n (it.json, en.json)
  - `styles/` — Tailwind config, global CSS
- `frontend/package.json` — dipendenze Node.js
- `frontend/tsconfig.json` — configurazione TypeScript
- `frontend/next.config.ts` — configurazione Next.js

### Cosa NON toccare

- Backend (`backend/`)
- Docker/CI (`.github/workflows/`, `docker-compose.yml`)
- Modelli dati e API — consuma solo il contratto OpenAPI

## Issues assegnate (Ciclo 1)

- **#15** — [Frontend] Next.js setup + Tailwind + Shadcn + i18n + Clerk
- **#16** — [Frontend] Dashboard page
- **#17** — [Frontend] Upload flow (drag & drop + preview)
- **#18** — [Frontend] Transactions list page
- **#19** — [Frontend] Categories management page
- **#20** — [Frontend] Analytics page (charts)
- **#21** — [Frontend] Accounts management + Export page

## Stack & Convenzioni

### Tecnologie

- Next.js 14+ (App Router), TypeScript strict
- Tailwind CSS 3+, Shadcn/UI
- Recharts per grafici
- Zustand per state management
- TanStack Query (React Query) per data fetching
- next-intl per i18n (IT + EN)
- React Dropzone per upload
- Clerk per autenticazione (@clerk/nextjs)

### Struttura directory

```
frontend/src/
├── app/
│   ├── [locale]/
│   │   ├── layout.tsx        # Root layout con ClerkProvider + QueryProvider
│   │   ├── page.tsx          # Redirect a /dashboard
│   │   ├── (auth)/
│   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   └── sign-up/[[...sign-up]]/page.tsx
│   │   ├── (app)/
│   │   │   ├── layout.tsx    # App layout con sidebar
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── transactions/page.tsx
│   │   │   ├── upload/page.tsx
│   │   │   ├── categories/page.tsx
│   │   │   ├── analytics/page.tsx
│   │   │   ├── accounts/page.tsx
│   │   │   └── export/page.tsx
│   │   └── middleware.ts
│   └── globals.css
├── components/
│   ├── ui/                   # Shadcn components (auto-generated)
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Navbar.tsx
│   │   └── Footer.tsx
│   ├── dashboard/
│   │   ├── BalanceCard.tsx
│   │   ├── ExpenseChart.tsx
│   │   └── RecentTransactions.tsx
│   ├── transactions/
│   │   ├── TransactionTable.tsx
│   │   ├── TransactionFilters.tsx
│   │   └── CategorySelect.tsx
│   ├── upload/
│   │   ├── DropZone.tsx
│   │   ├── PreviewTable.tsx
│   │   └── ImportSummary.tsx
│   └── common/
│       ├── AmountDisplay.tsx
│       ├── DateDisplay.tsx
│       └── LoadingSkeleton.tsx
├── lib/
│   ├── api.ts               # API client (fetch wrapper)
│   ├── utils.ts             # Utility generiche
│   └── formatters.ts        # Formattazione importi, date
├── stores/
│   └── app-store.ts         # Zustand global store
├── messages/
│   ├── it.json              # Traduzioni italiano
│   └── en.json              # Traduzioni inglese
└── types/
    ├── api.ts               # Tipi derivati da OpenAPI
    └── index.ts
```

### Design System

- **Colori primari**: Teal (`#0D9488` / `teal-600`)
- **Background**: `slate-50` (light), `slate-900` (dark, futuro)
- **Testo**: `slate-900` (titoli), `slate-600` (body)
- **Positivo**: `emerald-500` (income)
- **Negativo**: `rose-500` (expense)
- **Font**: Inter (sans-serif)
- **Spacing**: 4px grid (p-1 = 4px, p-2 = 8px, ecc.)
- **Border radius**: `rounded-lg` di default

### Pattern

- **Data fetching**: TanStack Query con `useQuery` / `useMutation`
- **Stato globale**: Zustand per UI state (sidebar, filters)
- **Componenti**: functional components con TypeScript props interface
- **Loading**: Skeleton components (Shadcn Skeleton)
- **Errori**: Error boundary + toast notifications (Shadcn Sonner)
- **Forms**: React Hook Form + Zod validation
- **i18n**: `useTranslations('namespace')` da next-intl

### Formattazione importi

```typescript
// Sempre con segno e colore
// +€1.234,56 (verde) per income
// -€987,65 (rosso) per expense
const formatAmount = (amount: number, locale: string = "it-IT") =>
  new Intl.NumberFormat(locale, { style: "currency", currency: "EUR" }).format(
    amount,
  );
```

### Testing

- Vitest + @testing-library/react per unit test
- Playwright per E2E (coordinato con DevSecOps)
- Test componenti principali: rendering, interazione, stati loading/error
- Naming: `ComponentName.test.tsx`

## Contratto API

- Consuma `backend/openapi.yaml` come source of truth
- I tipi TypeScript in `types/api.ts` devono riflettere l'OpenAPI spec
- Se l'API non è pronta, usa mock data (`lib/mock-data.ts`)

## Dipendenze

- **Da**: Backend (API contract deve essere definito prima)
- **Da**: DevSecOps (struttura monorepo e Docker)
- **Verso**: nessuno
