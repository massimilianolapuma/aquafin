"use client";

import { useState, useCallback } from "react";
import { useTranslations } from "next-intl";
import { Trash2, Tag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatDate } from "@/lib/format";

import { CategoryEditPopover } from "./category-edit-popover";
import type { Transaction, AccountOption, CategoryOption } from "./transactions-view";

interface TransactionsTableProps {
  transactions: Transaction[];
  categories: CategoryOption[];
  accounts: AccountOption[];
  selectedIds: Set<number>;
  onToggleSelect: (id: number) => void;
  onToggleAll: () => void;
  onRecategorize: (
    transactionId: number,
    categoryId: number,
    applyToSimilar: boolean,
  ) => void;
  onBulkCategorize: (categoryId: number) => void;
  onBulkDelete: () => void;
}

/**
 * HTML table displaying transactions with selection, inline category editing,
 * and a bulk-action bar.
 */
export function TransactionsTable({
  transactions,
  categories,
  accounts,
  selectedIds,
  onToggleSelect,
  onToggleAll,
  onRecategorize,
  onBulkCategorize,
  onBulkDelete,
}: TransactionsTableProps) {
  const t = useTranslations("transactions");

  // Which transaction currently has the category popover open
  const [editingCategoryTxId, setEditingCategoryTxId] = useState<number | null>(null);

  // Bulk-category popover
  const [showBulkCategoryPopover, setShowBulkCategoryPopover] = useState(false);

  // Confirm delete state
  const [confirmDelete, setConfirmDelete] = useState(false);

  const allSelected =
    transactions.length > 0 && selectedIds.size === transactions.length;

  const getCategoryName = useCallback(
    (id: number | null) => {
      if (id === null) return t("uncategorized");
      return categories.find((c) => c.id === id)?.name ?? t("uncategorized");
    },
    [categories, t],
  );

  const getCategoryColor = useCallback(
    (id: number | null) => {
      if (id === null) return "#9E9E9E";
      return categories.find((c) => c.id === id)?.color ?? "#9E9E9E";
    },
    [categories],
  );

  const getAccountName = useCallback(
    (id: number | null) => {
      if (id === null) return "—";
      return accounts.find((a) => a.id === id)?.name ?? "—";
    },
    [accounts],
  );

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
    <div>
      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 border-b border-slate-200 bg-teal-50 px-6 py-2">
          <span className="text-sm font-medium text-teal-800">
            {t("selectedCount", { count: selectedIds.size })}
          </span>
          <div className="flex-1" />
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowBulkCategoryPopover(!showBulkCategoryPopover)}
            >
              <Tag className="mr-1.5 h-3.5 w-3.5" />
              {t("bulkCategorize")}
            </Button>
            {showBulkCategoryPopover && (
              <CategoryEditPopover
                currentCategoryId={null}
                categories={categories}
                onConfirm={(catId) => {
                  onBulkCategorize(catId);
                  setShowBulkCategoryPopover(false);
                }}
                onClose={() => setShowBulkCategoryPopover(false)}
              />
            )}
          </div>
          {confirmDelete ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-600">{t("confirmDelete")}</span>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => {
                  onBulkDelete();
                  setConfirmDelete(false);
                }}
              >
                {t("confirmAction")}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmDelete(false)}
              >
                {t("cancelAction")}
              </Button>
            </div>
          ) : (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmDelete(true)}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              {t("bulkDelete")}
            </Button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs font-medium uppercase tracking-wider text-slate-500">
              <th className="px-6 py-3 w-10">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={onToggleAll}
                  className="rounded border-slate-300"
                />
              </th>
              <th className="px-3 py-3">{t("date")}</th>
              <th className="px-3 py-3">{t("description")}</th>
              <th className="px-3 py-3 text-right">{t("amount")}</th>
              <th className="px-3 py-3">{t("account")}</th>
              <th className="px-3 py-3">{t("category")}</th>
              <th className="px-3 py-3">{t("type")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {transactions.map((tx) => {
              const isSelected = selectedIds.has(tx.id);
              return (
                <tr
                  key={tx.id}
                  className={`transition-colors hover:bg-slate-50 ${
                    isSelected ? "bg-teal-50/50" : ""
                  }`}
                >
                  {/* Checkbox */}
                  <td className="px-6 py-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelect(tx.id)}
                      className="rounded border-slate-300"
                    />
                  </td>

                  {/* Date */}
                  <td className="whitespace-nowrap px-3 py-3 text-slate-600">
                    {formatDate(tx.date)}
                  </td>

                  {/* Description */}
                  <td className="max-w-xs truncate px-3 py-3 font-medium text-slate-900">
                    {tx.description}
                  </td>

                  {/* Amount */}
                  <td
                    className={`whitespace-nowrap px-3 py-3 text-right font-semibold ${
                      tx.type === "income"
                        ? "text-emerald-600"
                        : tx.type === "expense"
                          ? "text-rose-600"
                          : "text-slate-600"
                    }`}
                  >
                    {tx.type === "income" ? "+" : tx.type === "expense" ? "-" : ""}
                    {formatCurrency(Math.abs(tx.amount))}
                  </td>

                  {/* Account */}
                  <td className="whitespace-nowrap px-3 py-3 text-slate-600">
                    {getAccountName(tx.account_id)}
                  </td>

                  {/* Category badge — clickable for inline edit */}
                  <td className="relative px-3 py-3">
                    <button
                      onClick={() =>
                        setEditingCategoryTxId(
                          editingCategoryTxId === tx.id ? null : tx.id,
                        )
                      }
                      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors hover:ring-2 hover:ring-teal-200"
                      style={{
                        backgroundColor: `${getCategoryColor(tx.category_id)}20`,
                        color: getCategoryColor(tx.category_id),
                      }}
                    >
                      <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{
                          backgroundColor: getCategoryColor(tx.category_id),
                        }}
                      />
                      {getCategoryName(tx.category_id)}
                    </button>

                    {editingCategoryTxId === tx.id && (
                      <CategoryEditPopover
                        currentCategoryId={tx.category_id}
                        categories={categories}
                        onConfirm={(catId, applyToSimilar) => {
                          onRecategorize(tx.id, catId, applyToSimilar);
                          setEditingCategoryTxId(null);
                        }}
                        onClose={() => setEditingCategoryTxId(null)}
                      />
                    )}
                  </td>

                  {/* Type */}
                  <td className="whitespace-nowrap px-3 py-3">
                    <span
                      className={`text-xs font-medium ${
                        tx.type === "income"
                          ? "text-emerald-600"
                          : tx.type === "expense"
                            ? "text-rose-600"
                            : "text-slate-500"
                      }`}
                    >
                      {typeLabel(tx.type)}
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
