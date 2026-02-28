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
import type { CategoryBreakdown } from "@/lib/mock-data";

interface CategoryChartProps {
  data: CategoryBreakdown[];
}

/** Donut chart showing expense breakdown by category. */
export function CategoryChart({ data }: CategoryChartProps) {
  const t = useTranslations("dashboard");

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">{t("categoryBreakdown")}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 pb-6">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              nameKey="name"
              stroke="none"
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                fontSize: "13px",
              }}
            />
            <Legend
              verticalAlign="bottom"
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for the category chart. */
export function CategoryChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-4 w-40 animate-pulse rounded bg-slate-100" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center h-[280px]">
          <div className="h-[200px] w-[200px] animate-pulse rounded-full bg-slate-100" />
        </div>
      </CardContent>
    </Card>
  );
}
