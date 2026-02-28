"use client";

import {
  ComposedChart,
  Bar,
  Line,
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

export interface MonthlyBarItem {
  month: string;
  income: number;
  expenses: number;
  balance: number;
}

interface MonthlyBarChartProps {
  data: MonthlyBarItem[];
}

// ---------- Helpers ----------

/** Convert "2025-01" → "Jan 25" */
function shortMonth(ym: string): string {
  const [year, month] = ym.split("-");
  const d = new Date(Number(year), Number(month) - 1, 1);
  return d.toLocaleDateString("en", { month: "short", year: "2-digit" });
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

/** Grouped bar chart with income/expense bars and a net line overlay. */
export function MonthlyBarChart({ data }: MonthlyBarChartProps) {
  const t = useTranslations("analytics");

  const chartData = data.map((item) => ({
    ...item,
    label: shortMonth(item.month),
  }));

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">{t("monthlyTrend")}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-6">
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-[300px] text-sm text-slate-400">
            {t("noData")}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="label"
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
                dataKey="income"
                name={t("income")}
                fill="#10b981"
                radius={[4, 4, 0, 0]}
                maxBarSize={36}
              />
              <Bar
                dataKey="expenses"
                name={t("expenses")}
                fill="#f43f5e"
                radius={[4, 4, 0, 0]}
                maxBarSize={36}
              />
              <Line
                dataKey="balance"
                name={t("net")}
                type="monotone"
                stroke="#0d9488"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for the monthly bar chart. */
export function MonthlyBarChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-4 w-36 animate-pulse rounded bg-slate-100" />
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-2 h-[300px] pt-8">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="flex-1 animate-pulse rounded bg-slate-100"
              style={{ height: `${40 + Math.random() * 50}%` }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
