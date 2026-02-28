"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useTranslations } from "next-intl";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";

// ---------- Color palette for categories ----------
const COLORS = [
  "#0d9488",
  "#10b981",
  "#f59e0b",
  "#f43f5e",
  "#8b5cf6",
  "#3b82f6",
  "#ec4899",
  "#14b8a6",
  "#6366f1",
  "#ef4444",
  "#22c55e",
  "#a855f7",
];

// ---------- Types ----------

export interface CategoryPieItem {
  category_name: string;
  total: number;
  count: number;
  percentage: number;
}

interface CategoryPieChartProps {
  data: CategoryPieItem[];
}

// ---------- Custom tooltip ----------

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: { percentage: number; count: number };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md text-sm">
      <p className="font-medium text-slate-900">{item.name}</p>
      <p className="text-slate-600">{formatCurrency(item.value)}</p>
      <p className="text-slate-400">
        {item.payload.percentage.toFixed(1)}% · {item.payload.count} txn
      </p>
    </div>
  );
}

// ---------- Component ----------

/** Donut chart showing expense breakdown by category with inner total label. */
export function CategoryPieChart({ data }: CategoryPieChartProps) {
  const t = useTranslations("analytics");

  const chartData = data.map((item, idx) => ({
    name: item.category_name,
    value: item.total,
    percentage: item.percentage,
    count: item.count,
    fill: COLORS[idx % COLORS.length],
  }));

  const total = data.reduce((sum, d) => sum + d.total, 0);

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">{t("categoryBreakdown")}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-6">
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-[300px] text-sm text-slate-400">
            {t("noData")}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={105}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
                stroke="none"
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Pie>
              {/* Center label */}
              <text
                x="50%"
                y="48%"
                textAnchor="middle"
                dominantBaseline="central"
                className="fill-slate-900 text-lg font-bold"
              >
                {formatCurrency(total)}
              </text>
              <text
                x="50%"
                y="56%"
                textAnchor="middle"
                dominantBaseline="central"
                className="fill-slate-400 text-xs"
              >
                {t("total")}
              </text>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for the category pie chart. */
export function CategoryPieChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-4 w-44 animate-pulse rounded bg-slate-100" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center h-[300px]">
          <div className="h-[200px] w-[200px] animate-pulse rounded-full bg-slate-100" />
        </div>
      </CardContent>
    </Card>
  );
}
