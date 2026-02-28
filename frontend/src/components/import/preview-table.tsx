"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { AlertTriangle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { formatCurrency, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Shape of a single parsed transaction returned by the API preview. */
export interface PreviewTransaction {
  temp_id: string;
  date: string;
  amount: number;
  currency: string;
  description: string;
  original_description: string;
  type: "income" | "expense" | "transfer";
  category_name: string | null;
  confidence: number;
  matched_by: string | null;
}

interface PreviewTableProps {
  transactions: PreviewTransaction[];
  errors: string[];
  /** Map of temp_id → overridden category name. */
  categoryOverrides: Record<string, string>;
  onCategoryOverride: (tempId: string, category: string) => void;
}

/** Confidence colour helper. */
function confidenceColor(c: number) {
  if (c >= 0.7) return "bg-emerald-500";
  if (c >= 0.4) return "bg-amber-400";
  return "bg-rose-500";
}

function confidenceLabel(c: number, t: (key: string) => string) {
  if (c >= 0.7) return t("highConfidence");
  if (c >= 0.4) return t("mediumConfidence");
  return t("lowConfidence");
}

/** Table displaying parsed transactions with inline category editing. */
export function PreviewTable({
  transactions,
  errors,
  categoryOverrides,
  onCategoryOverride,
}: PreviewTableProps) {
  const t = useTranslations("upload");
  const [editingId, setEditingId] = useState<string | null>(null);

  const typeLabel = (type: string) => {
    switch (type) {
      case "income":
        return t("income");
      case "expense":
        return t("expense");
      case "transfer":
        return t("transfer");
      default:
        return type;
    }
  };

  return (
    <div className="space-y-4">
      {/* Row count */}
      <p className="text-sm text-slate-600">
        {t("previewSubtitle", { count: transactions.length })}
      </p>

      {/* Parsing errors */}
      {errors.length > 0 && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3">
          <div className="mb-1 flex items-center gap-2 text-sm font-medium text-amber-800">
            <AlertTriangle className="h-4 w-4" />
            {t("parsingErrors")}
          </div>
          <ul className="list-inside list-disc text-xs text-amber-700">
            {errors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">{t("date")}</th>
              <th className="px-4 py-3">{t("description")}</th>
              <th className="px-4 py-3 text-right">{t("amount")}</th>
              <th className="px-4 py-3">{t("type")}</th>
              <th className="px-4 py-3">{t("category")}</th>
              <th className="px-4 py-3">{t("confidence")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transactions.map((tx) => {
              const overridden = categoryOverrides[tx.temp_id];
              const displayCategory = overridden ?? tx.category_name ?? "—";
              const isEditing = editingId === tx.temp_id;

              return (
                <tr key={tx.temp_id} className="hover:bg-slate-50/60">
                  <td className="whitespace-nowrap px-4 py-2.5 text-slate-700">
                    {formatDate(tx.date)}
                  </td>
                  <td
                    className="max-w-[240px] truncate px-4 py-2.5 text-slate-700"
                    title={tx.original_description}
                  >
                    {tx.description}
                  </td>
                  <td
                    className={cn(
                      "whitespace-nowrap px-4 py-2.5 text-right font-medium",
                      tx.type === "income"
                        ? "text-emerald-600"
                        : "text-rose-600",
                    )}
                  >
                    {formatCurrency(tx.amount)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={cn(
                        "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
                        tx.type === "income"
                          ? "bg-emerald-100 text-emerald-700"
                          : tx.type === "transfer"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-rose-100 text-rose-700",
                      )}
                    >
                      {typeLabel(tx.type)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    {isEditing ? (
                      <Input
                        autoFocus
                        defaultValue={displayCategory}
                        className="h-7 w-32 text-xs"
                        onBlur={(e) => {
                          const val = e.target.value.trim();
                          if (val && val !== tx.category_name) {
                            onCategoryOverride(tx.temp_id, val);
                          }
                          setEditingId(null);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            (e.target as HTMLInputElement).blur();
                          }
                          if (e.key === "Escape") {
                            setEditingId(null);
                          }
                        }}
                      />
                    ) : (
                      <button
                        type="button"
                        onClick={() => setEditingId(tx.temp_id)}
                        className="inline-block rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 hover:bg-slate-200"
                        title={t("category")}
                      >
                        {displayCategory}
                      </button>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="flex items-center gap-1.5 text-xs text-slate-600">
                      <span
                        className={cn(
                          "inline-block h-2 w-2 rounded-full",
                          confidenceColor(tx.confidence),
                        )}
                      />
                      {confidenceLabel(tx.confidence, t)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
