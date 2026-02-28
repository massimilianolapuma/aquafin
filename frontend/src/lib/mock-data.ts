/**
 * Mock data for the dashboard.
 * Will be replaced with real API calls once the backend endpoints are ready.
 */

export interface CategoryBreakdown {
  name: string;
  value: number;
  color: string;
}

export interface MonthlyTrend {
  month: string;
  income: number;
  expenses: number;
}

export interface RecentTransaction {
  id: string;
  date: string;
  description: string;
  category: string;
  amount: number;
  type: "income" | "expense";
}

export interface DashboardData {
  balance: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  savingsRate: number;
  categoryBreakdown: CategoryBreakdown[];
  monthlyTrend: MonthlyTrend[];
  recentTransactions: RecentTransaction[];
}

export const MOCK_DASHBOARD: DashboardData = {
  balance: 12450.8,
  monthlyIncome: 2850.0,
  monthlyExpenses: 1920.45,
  savingsRate: 32.6,

  categoryBreakdown: [
    { name: "Alimentari", value: 480.5, color: "#4CAF50" },
    { name: "Casa", value: 650.0, color: "#2196F3" },
    { name: "Trasporti", value: 280.3, color: "#FF9800" },
    { name: "Svago", value: 150.0, color: "#E91E63" },
    { name: "Servizi", value: 120.0, color: "#00BCD4" },
    { name: "Salute", value: 89.5, color: "#F44336" },
    { name: "Shopping", value: 110.15, color: "#9C27B0" },
    { name: "Altro", value: 40.0, color: "#9E9E9E" },
  ],

  monthlyTrend: [
    { month: "Set", income: 2800, expenses: 2100 },
    { month: "Ott", income: 2850, expenses: 1950 },
    { month: "Nov", income: 2800, expenses: 2200 },
    { month: "Dic", income: 3200, expenses: 2500 },
    { month: "Gen", income: 2850, expenses: 1800 },
    { month: "Feb", income: 2850, expenses: 1920 },
  ],

  recentTransactions: [
    {
      id: "1",
      date: "2025-02-28",
      description: "PAGAMENTO POS ESSELUNGA",
      category: "Supermercato",
      amount: -45.8,
      type: "expense",
    },
    {
      id: "2",
      date: "2025-02-27",
      description: "BONIFICO STIPENDIO MARZO",
      category: "Stipendio",
      amount: 2850.0,
      type: "income",
    },
    {
      id: "3",
      date: "2025-02-25",
      description: "ADDEBITO SDD ENEL ENERGIA",
      category: "Utenze",
      amount: -89.5,
      type: "expense",
    },
    {
      id: "4",
      date: "2025-02-24",
      description: "Netflix",
      category: "Abbonamenti",
      amount: -15.99,
      type: "expense",
    },
    {
      id: "5",
      date: "2025-02-23",
      description: "PRELIEVO BANCOMAT",
      category: "Altro",
      amount: -200.0,
      type: "expense",
    },
    {
      id: "6",
      date: "2025-02-20",
      description: "Farmacia Comunale",
      category: "Farmacia",
      amount: -32.5,
      type: "expense",
    },
    {
      id: "7",
      date: "2025-02-18",
      description: "POS AMAZON EU",
      category: "Elettronica",
      amount: -59.99,
      type: "expense",
    },
    {
      id: "8",
      date: "2025-02-15",
      description: "Bar Roma (Satispay)",
      category: "Bar/Caffè",
      amount: -4.5,
      type: "expense",
    },
    {
      id: "9",
      date: "2025-02-12",
      description: "GIROCONTO DA DEPOSITO",
      category: "Altro",
      amount: 500.0,
      type: "income",
    },
    {
      id: "10",
      date: "2025-02-10",
      description: "Spotify Premium",
      category: "Abbonamenti",
      amount: -9.99,
      type: "expense",
    },
  ],
};
