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
import type { MonthlyTrend } from "@/lib/mock-data";

interface MonthlyChartProps {
  data: MonthlyTrend[];
}

/** Bar chart showing monthly income vs expenses trend. */
export function MonthlyChart({ data }: MonthlyChartProps) {
  const t = useTranslations("dashboard");

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">{t("monthlyTrend")}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-6">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#64748b" }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: "#64748b" }}
              tickFormatter={(v: number) => `€${(v / 1000).toFixed(1)}k`}
            />
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                fontSize: "13px",
              }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
            />
            <Bar
              dataKey="income"
              name={t("income")}
              fill="#10B981"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
            <Bar
              dataKey="expenses"
              name={t("expenses")}
              fill="#F43F5E"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for the monthly chart. */
export function MonthlyChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-4 w-36 animate-pulse rounded bg-slate-100" />
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between gap-2 h-[280px] px-4 pb-8">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex gap-1 flex-1">
              <div
                className="flex-1 animate-pulse rounded bg-slate-100"
                style={{ height: `${100 + Math.random() * 120}px` }}
              />
              <div
                className="flex-1 animate-pulse rounded bg-slate-100"
                style={{ height: `${80 + Math.random() * 100}px` }}
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
