"use client";

import { useTranslations } from "next-intl";
import { Wallet, TrendingUp, TrendingDown, PiggyBank } from "lucide-react";
import { StatCard } from "@/components/dashboard/stat-card";
import { CategoryChart } from "@/components/dashboard/category-chart";
import { MonthlyChart } from "@/components/dashboard/monthly-chart";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { formatCurrency, formatPercent } from "@/lib/format";
import { MOCK_DASHBOARD } from "@/lib/mock-data";

/** Client component rendering the full dashboard view with mock data. */
export function DashboardView() {
  const t = useTranslations("dashboard");
  const data = MOCK_DASHBOARD;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
        <p className="text-sm text-slate-500">
          {new Intl.DateTimeFormat("it-IT", {
            month: "long",
            year: "numeric",
          }).format(new Date())}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title={t("balance")}
          value={formatCurrency(data.balance)}
          icon={Wallet}
          variant="default"
        />
        <StatCard
          title={t("income")}
          value={formatCurrency(data.monthlyIncome)}
          icon={TrendingUp}
          variant="income"
          trend={{ value: 1.8, label: "vs mese precedente" }}
        />
        <StatCard
          title={t("expenses")}
          value={formatCurrency(data.monthlyExpenses)}
          icon={TrendingDown}
          variant="expense"
          trend={{ value: -6.7, label: "vs mese precedente" }}
        />
        <StatCard
          title={t("savingsRate")}
          value={formatPercent(data.savingsRate)}
          icon={PiggyBank}
          variant="default"
          trend={{ value: 4.2, label: "vs mese precedente" }}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <CategoryChart data={data.categoryBreakdown} />
        <MonthlyChart data={data.monthlyTrend} />
      </div>

      {/* Recent transactions + quick actions */}
      <div className="space-y-4">
        <RecentTransactions transactions={data.recentTransactions} />
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-500">
            {t("quickActions")}
          </h2>
          <QuickActions />
        </div>
      </div>
    </div>
  );
}
