"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useTranslations } from "next-intl";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";

// ---------- Types ----------

export interface AccountStackedItem {
  account_name: string;
  total_income: number;
  total_expenses: number;
  balance: number;
}

interface AccountStackedChartProps {
  data: AccountStackedItem[];
}

// ---------- Custom tooltip ----------

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md text-sm">
      <p className="font-medium text-slate-700 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {formatCurrency(p.value)}
        </p>
      ))}
    </div>
  );
}

// ---------- Component ----------

/** Stacked bar chart showing income and expenses per account. */
export function AccountStackedChart({ data }: AccountStackedChartProps) {
  const t = useTranslations("analytics");

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">{t("accountBreakdown")}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-6">
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-[300px] text-sm text-slate-400">
            {t("noData")}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="account_name"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 12, fill: "#64748b" }}
                tickFormatter={(v: number) =>
                  v >= 1000 || v <= -1000
                    ? `€${(v / 1000).toFixed(1)}k`
                    : `€${v}`
                }
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
              />
              <Bar
                dataKey="total_income"
                name={t("income")}
                stackId="a"
                fill="#10b981"
                radius={[0, 0, 0, 0]}
                maxBarSize={48}
              />
              <Bar
                dataKey="total_expenses"
                name={t("expenses")}
                stackId="a"
                fill="#f43f5e"
                radius={[4, 4, 0, 0]}
                maxBarSize={48}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for the account stacked chart. */
export function AccountStackedChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-4 w-40 animate-pulse rounded bg-slate-100" />
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-4 h-[300px] pt-8">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="flex-1 animate-pulse rounded bg-slate-100"
              style={{ height: `${50 + Math.random() * 40}%` }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
