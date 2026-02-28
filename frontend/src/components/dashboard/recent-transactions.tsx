"use client";

import { useTranslations } from "next-intl";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatCurrency, formatDate } from "@/lib/format";
import type { RecentTransaction as TransactionType } from "@/lib/mock-data";

interface RecentTransactionsProps {
  transactions: TransactionType[];
}

/** List of the most recent transactions with category badges. */
export function RecentTransactions({ transactions }: RecentTransactionsProps) {
  const t = useTranslations("dashboard");

  if (transactions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {t("recentTransactions")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-400 text-center py-8">
            {t("noTransactions")}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">{t("recentTransactions")}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {transactions.map((tx) => (
            <div
              key={tx.id}
              className="flex items-center gap-3 rounded-lg px-2 py-2.5 hover:bg-slate-50 transition-colors"
            >
              {/* Date */}
              <span className="hidden sm:block w-20 shrink-0 text-xs text-slate-400 font-mono">
                {formatDate(tx.date)}
              </span>

              {/* Description + category */}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-700 truncate">
                  {tx.description}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="sm:hidden text-xs text-slate-400 font-mono">
                    {formatDate(tx.date)}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                    {tx.category}
                  </span>
                </div>
              </div>

              {/* Amount */}
              <span
                className={cn(
                  "shrink-0 text-sm font-semibold font-mono tabular-nums",
                  tx.type === "income" ? "text-emerald-600" : "text-rose-600",
                )}
              >
                {tx.type === "income" ? "+" : ""}
                {formatCurrency(tx.amount)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/** Loading skeleton for recent transactions. */
export function RecentTransactionsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-4 w-40 animate-pulse rounded bg-slate-100" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 py-2">
              <div className="hidden sm:block h-3 w-20 animate-pulse rounded bg-slate-100" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-3/4 animate-pulse rounded bg-slate-100" />
                <div className="h-2.5 w-16 animate-pulse rounded bg-slate-100" />
              </div>
              <div className="h-3 w-16 animate-pulse rounded bg-slate-100" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
