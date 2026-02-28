"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  /** Card title label */
  title: string;
  /** Formatted value to display */
  value: string;
  /** Lucide icon component */
  icon: React.ComponentType<{ className?: string }>;
  /** Optional trend indicator (e.g., +5% vs last month) */
  trend?: { value: number; label: string };
  /** Color variant for the icon/accent */
  variant?: "default" | "income" | "expense";
}

const variantStyles = {
  default: {
    iconBg: "bg-primary-50",
    iconColor: "text-primary-600",
  },
  income: {
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
  },
  expense: {
    iconBg: "bg-rose-50",
    iconColor: "text-rose-600",
  },
} as const;

/** Reusable stat card showing an icon, title, value, and optional trend. */
export function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  variant = "default",
}: StatCardProps) {
  const styles = variantStyles[variant];

  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
              styles.iconBg,
            )}
          >
            <Icon className={cn("h-5 w-5", styles.iconColor)} />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-slate-500 truncate">{title}</p>
            <p className="text-xl font-bold tracking-tight font-mono truncate">
              {value}
            </p>
          </div>
        </div>
        {trend && (
          <div className="mt-3 flex items-center gap-1 text-xs">
            <span
              className={cn(
                "font-medium",
                trend.value >= 0 ? "text-emerald-600" : "text-rose-600",
              )}
            >
              {trend.value >= 0 ? "+" : ""}
              {trend.value.toFixed(1)}%
            </span>
            <span className="text-slate-400">{trend.label}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for the stat card. */
export function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 animate-pulse rounded-lg bg-slate-100" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-20 animate-pulse rounded bg-slate-100" />
            <div className="h-5 w-28 animate-pulse rounded bg-slate-100" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
