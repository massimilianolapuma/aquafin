"use client";

import { useState, useMemo, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  TrendingDown,
  PiggyBank,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  CalendarDays,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/format";

import {
  CategoryPieChart,
  CategoryPieChartSkeleton,
  type CategoryPieItem,
} from "@/components/analytics/category-pie-chart";
import {
  MonthlyBarChart,
  MonthlyBarChartSkeleton,
  type MonthlyBarItem,
} from "@/components/analytics/monthly-bar-chart";
import {
  AccountStackedChart,
  AccountStackedChartSkeleton,
  type AccountStackedItem,
} from "@/components/analytics/account-stacked-chart";
import {
  TrendLineChart,
  TrendLineChartSkeleton,
  type TrendLineItem,
} from "@/components/analytics/trend-line-chart";

// ---------------------------------------------------------------------------
// API response types (matching backend schemas)
// ---------------------------------------------------------------------------

interface AnalyticsSummary {
  total_income: number;
  total_expenses: number;
  balance: number;
  transaction_count: number;
  period_start: string;
  period_end: string;
}

interface CategoryBreakdownResponse {
  items: CategoryPieItem[];
  total_expenses: number;
  period_start: string;
  period_end: string;
}

interface MonthlyTrendResponse {
  items: MonthlyBarItem[];
}

interface AccountBreakdownResponse {
  items: AccountStackedItem[];
}

interface Account {
  id: string;
  name: string;
}

// ---------------------------------------------------------------------------
// Period helpers
// ---------------------------------------------------------------------------

type PeriodType = "month" | "quarter" | "year" | "custom";

function periodDates(type: PeriodType, customFrom?: string, customTo?: string) {
  const now = new Date();
  let dateFrom: string;
  let dateTo: string;

  switch (type) {
    case "month": {
      const y = now.getFullYear();
      const m = now.getMonth();
      dateFrom = new Date(y, m, 1).toISOString().slice(0, 10);
      dateTo = new Date(y, m + 1, 0).toISOString().slice(0, 10);
      break;
    }
    case "quarter": {
      const y = now.getFullYear();
      const q = Math.floor(now.getMonth() / 3);
      dateFrom = new Date(y, q * 3, 1).toISOString().slice(0, 10);
      dateTo = new Date(y, q * 3 + 3, 0).toISOString().slice(0, 10);
      break;
    }
    case "year": {
      const y = now.getFullYear();
      dateFrom = `${y}-01-01`;
      dateTo = `${y}-12-31`;
      break;
    }
    case "custom":
      dateFrom = customFrom ?? new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
      dateTo = customTo ?? now.toISOString().slice(0, 10);
      break;
  }

  return { dateFrom, dateTo };
}

/** Shift a period range backwards by its own length for comparison. */
function previousPeriodDates(dateFrom: string, dateTo: string) {
  const from = new Date(dateFrom);
  const to = new Date(dateTo);
  const diff = to.getTime() - from.getTime();
  const prevTo = new Date(from.getTime() - 1); // day before current period start
  const prevFrom = new Date(prevTo.getTime() - diff);
  return {
    dateFrom: prevFrom.toISOString().slice(0, 10),
    dateTo: prevTo.toISOString().slice(0, 10),
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/** Main analytics page view with filters, stats, charts and period comparison. */
export function AnalyticsView() {
  const t = useTranslations("analytics");
  const { getToken } = useAuth();

  // --- Filter state ---
  const [period, setPeriod] = useState<PeriodType>("month");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [accountId, setAccountId] = useState<string>("");

  const { dateFrom, dateTo } = useMemo(
    () => periodDates(period, customFrom, customTo),
    [period, customFrom, customTo],
  );

  const prevPeriod = useMemo(
    () => previousPeriodDates(dateFrom, dateTo),
    [dateFrom, dateTo],
  );

  // --- Query param builder ---
  const buildParams = useCallback(
    (from: string, to: string) => {
      const params = new URLSearchParams({ date_from: from, date_to: to });
      if (accountId) params.set("account_id", accountId);
      return params.toString();
    },
    [accountId],
  );

  // --- Data fetching ---
  const queryOpts = { staleTime: 30_000, retry: 1 };

  const summaryQuery = useQuery<AnalyticsSummary>({
    queryKey: ["analytics", "summary", dateFrom, dateTo, accountId],
    queryFn: async () => {
      const token = (await getToken()) ?? undefined;
      return api.get<AnalyticsSummary>(
        `/analytics/summary?${buildParams(dateFrom, dateTo)}`,
        { token },
      );
    },
    ...queryOpts,
  });

  const prevSummaryQuery = useQuery<AnalyticsSummary>({
    queryKey: ["analytics", "summary", prevPeriod.dateFrom, prevPeriod.dateTo, accountId],
    queryFn: async () => {
      const token = (await getToken()) ?? undefined;
      return api.get<AnalyticsSummary>(
        `/analytics/summary?${buildParams(prevPeriod.dateFrom, prevPeriod.dateTo)}`,
        { token },
      );
    },
    ...queryOpts,
  });

  const categoryQuery = useQuery<CategoryBreakdownResponse>({
    queryKey: ["analytics", "by-category", dateFrom, dateTo, accountId],
    queryFn: async () => {
      const token = (await getToken()) ?? undefined;
      return api.get<CategoryBreakdownResponse>(
        `/analytics/by-category?${buildParams(dateFrom, dateTo)}`,
        { token },
      );
    },
    ...queryOpts,
  });

  const monthlyQuery = useQuery<MonthlyTrendResponse>({
    queryKey: ["analytics", "by-month", dateFrom, dateTo, accountId],
    queryFn: async () => {
      const token = (await getToken()) ?? undefined;
      return api.get<MonthlyTrendResponse>(
        `/analytics/by-month?${buildParams(dateFrom, dateTo)}`,
        { token },
      );
    },
    ...queryOpts,
  });

  const accountQuery = useQuery<AccountBreakdownResponse>({
    queryKey: ["analytics", "by-account", dateFrom, dateTo, accountId],
    queryFn: async () => {
      const token = (await getToken()) ?? undefined;
      return api.get<AccountBreakdownResponse>(
        `/analytics/by-account?${buildParams(dateFrom, dateTo)}`,
        { token },
      );
    },
    ...queryOpts,
  });

  const accountsListQuery = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: async () => {
      const token = (await getToken()) ?? undefined;
      return api.get<Account[]>("/accounts", { token });
    },
    staleTime: 60_000,
  });

  // --- Derived values ---
  const summary = summaryQuery.data;
  const prevSummary = prevSummaryQuery.data;
  const isLoading = summaryQuery.isLoading;
  const isError = summaryQuery.isError;

  const savingsRate =
    summary && summary.total_income > 0
      ? ((summary.total_income - summary.total_expenses) / summary.total_income) * 100
      : 0;

  const prevSavingsRate =
    prevSummary && prevSummary.total_income > 0
      ? ((prevSummary.total_income - prevSummary.total_expenses) / prevSummary.total_income) * 100
      : 0;

  /** Calculate % change between current and previous values. */
  function delta(current: number, previous: number): number | null {
    if (previous === 0) return null;
    return ((current - previous) / Math.abs(previous)) * 100;
  }

  const incomeDelta = summary && prevSummary ? delta(summary.total_income, prevSummary.total_income) : null;
  const expensesDelta = summary && prevSummary ? delta(summary.total_expenses, prevSummary.total_expenses) : null;
  const netDelta = summary && prevSummary ? delta(summary.balance, prevSummary.balance) : null;
  const savingsDelta = delta(savingsRate, prevSavingsRate);

  // Use monthly data for trend line chart as well
  const trendData: TrendLineItem[] = useMemo(
    () =>
      (monthlyQuery.data?.items ?? []).map((m) => ({
        month: m.month,
        income: m.income,
        expenses: m.expenses,
        balance: m.balance,
      })),
    [monthlyQuery.data],
  );

  // --- Period button styles ---
  const periods: PeriodType[] = ["month", "quarter", "year", "custom"];

  return (
    <div className="space-y-6">
      {/* ---- Header ---- */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
          <p className="text-sm text-slate-500">{t("subtitle")}</p>
        </div>
      </div>

      {/* ---- Filters ---- */}
      <Card>
        <CardContent className="p-4 flex flex-wrap items-end gap-3">
          {/* Period selector */}
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-500">{t("period")}</span>
            <div className="flex gap-1">
              {periods.map((p) => (
                <Button
                  key={p}
                  variant={period === p ? "default" : "outline"}
                  size="sm"
                  onClick={() => setPeriod(p)}
                >
                  {t(`period_${p}`)}
                </Button>
              ))}
            </div>
          </div>

          {/* Custom date range */}
          {period === "custom" && (
            <div className="flex items-end gap-2">
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-500">{t("dateFrom")}</span>
                <Input
                  type="date"
                  value={customFrom}
                  onChange={(e) => setCustomFrom(e.target.value)}
                  className="w-36"
                />
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs font-medium text-slate-500">{t("dateTo")}</span>
                <Input
                  type="date"
                  value={customTo}
                  onChange={(e) => setCustomTo(e.target.value)}
                  className="w-36"
                />
              </div>
            </div>
          )}

          {/* Account filter */}
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-500">{t("account")}</span>
            <select
              className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 outline-none focus:ring-2 focus:ring-teal-500"
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
            >
              <option value="">{t("allAccounts")}</option>
              {(accountsListQuery.data ?? []).map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* ---- Error state ---- */}
      {isError && (
        <Card>
          <CardContent className="p-6 text-center text-rose-600">
            <p>{t("error")}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => summaryQuery.refetch()}
            >
              {t("retry")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* ---- Summary stat cards ---- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryStatCard
          title={t("totalIncome")}
          value={summary ? formatCurrency(summary.total_income) : "—"}
          icon={TrendingUp}
          delta={incomeDelta}
          deltaLabel={t("vsPrevious")}
          variant="income"
          loading={isLoading}
        />
        <SummaryStatCard
          title={t("totalExpenses")}
          value={summary ? formatCurrency(summary.total_expenses) : "—"}
          icon={TrendingDown}
          delta={expensesDelta}
          deltaLabel={t("vsPrevious")}
          variant="expense"
          loading={isLoading}
          invertDelta
        />
        <SummaryStatCard
          title={t("net")}
          value={summary ? formatCurrency(summary.balance) : "—"}
          icon={BarChart3}
          delta={netDelta}
          deltaLabel={t("vsPrevious")}
          variant="default"
          loading={isLoading}
        />
        <SummaryStatCard
          title={t("savingsRate")}
          value={summary ? formatPercent(savingsRate) : "—"}
          icon={PiggyBank}
          delta={savingsDelta}
          deltaLabel={t("vsPrevious")}
          variant="default"
          loading={isLoading}
        />
      </div>

      {/* ---- Charts grid ---- */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {categoryQuery.isLoading ? (
          <CategoryPieChartSkeleton />
        ) : (
          <CategoryPieChart data={categoryQuery.data?.items ?? []} />
        )}

        {monthlyQuery.isLoading ? (
          <MonthlyBarChartSkeleton />
        ) : (
          <MonthlyBarChart data={monthlyQuery.data?.items ?? []} />
        )}

        {accountQuery.isLoading ? (
          <AccountStackedChartSkeleton />
        ) : (
          <AccountStackedChart data={accountQuery.data?.items ?? []} />
        )}

        {monthlyQuery.isLoading ? (
          <TrendLineChartSkeleton />
        ) : (
          <TrendLineChart data={trendData} />
        )}
      </div>

      {/* ---- Period comparison ---- */}
      {summary && prevSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CalendarDays className="h-4 w-4 text-teal-600" />
              {t("periodComparison")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <ComparisonItem
                label={t("income")}
                current={summary.total_income}
                previous={prevSummary.total_income}
              />
              <ComparisonItem
                label={t("expenses")}
                current={summary.total_expenses}
                previous={prevSummary.total_expenses}
                invertColor
              />
              <ComparisonItem
                label={t("net")}
                current={summary.balance}
                previous={prevSummary.balance}
              />
              <ComparisonItem
                label={t("transactionCount")}
                current={summary.transaction_count}
                previous={prevSummary.transaction_count}
                isCurrency={false}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface SummaryStatCardProps {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  delta: number | null;
  deltaLabel: string;
  variant: "default" | "income" | "expense";
  loading: boolean;
  /** If true, a negative delta is shown as positive (lower expenses = good). */
  invertDelta?: boolean;
}

const variantStyles = {
  default: { iconBg: "bg-teal-50", iconColor: "text-teal-600" },
  income: { iconBg: "bg-emerald-50", iconColor: "text-emerald-600" },
  expense: { iconBg: "bg-rose-50", iconColor: "text-rose-600" },
} as const;

function SummaryStatCard({
  title,
  value,
  icon: Icon,
  delta,
  deltaLabel,
  variant,
  loading,
  invertDelta,
}: SummaryStatCardProps) {
  const styles = variantStyles[variant];
  const effectiveDelta = invertDelta && delta !== null ? -delta : delta;
  const isPositive = effectiveDelta !== null && effectiveDelta >= 0;

  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        {loading ? (
          <div className="space-y-2">
            <div className="h-3 w-24 animate-pulse rounded bg-slate-100" />
            <div className="h-6 w-32 animate-pulse rounded bg-slate-100" />
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3">
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${styles.iconBg}`}
              >
                <Icon className={`h-5 w-5 ${styles.iconColor}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm text-slate-500 truncate">{title}</p>
                <p className="text-xl font-bold tracking-tight font-mono truncate">
                  {value}
                </p>
              </div>
            </div>
            {delta !== null && (
              <div className="mt-3 flex items-center gap-1 text-xs">
                {isPositive ? (
                  <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600" />
                ) : (
                  <ArrowDownRight className="h-3.5 w-3.5 text-rose-600" />
                )}
                <span
                  className={`font-medium ${
                    isPositive ? "text-emerald-600" : "text-rose-600"
                  }`}
                >
                  {effectiveDelta !== null
                    ? `${effectiveDelta >= 0 ? "+" : ""}${effectiveDelta.toFixed(1)}%`
                    : ""}
                </span>
                <span className="text-slate-400">{deltaLabel}</span>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

interface ComparisonItemProps {
  label: string;
  current: number;
  previous: number;
  /** If true, lower current = green (e.g., expenses). */
  invertColor?: boolean;
  isCurrency?: boolean;
}

function ComparisonItem({
  label,
  current,
  previous,
  invertColor = false,
  isCurrency = true,
}: ComparisonItemProps) {
  const diff = current - previous;
  const pct = previous !== 0 ? (diff / Math.abs(previous)) * 100 : null;
  const isPositive = invertColor ? diff <= 0 : diff >= 0;

  return (
    <div className="rounded-lg border border-slate-100 p-3">
      <p className="text-xs font-medium text-slate-500 mb-1">{label}</p>
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-bold font-mono">
          {isCurrency ? formatCurrency(current) : current}
        </span>
        <span className="text-xs text-slate-400">
          vs {isCurrency ? formatCurrency(previous) : previous}
        </span>
      </div>
      {pct !== null && (
        <div className="mt-1 flex items-center gap-1 text-xs">
          {isPositive ? (
            <ArrowUpRight className="h-3 w-3 text-emerald-600" />
          ) : (
            <ArrowDownRight className="h-3 w-3 text-rose-600" />
          )}
          <span
            className={`font-medium ${
              isPositive ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {pct >= 0 ? "+" : ""}
            {pct.toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  );
}
