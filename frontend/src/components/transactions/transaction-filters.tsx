"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslations } from "next-intl";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import type { AccountOption, CategoryOption } from "./transactions-view";

/** Filter values shared between the filter bar and the parent view */
export interface TransactionFilterValues {
  search: string;
  accountId: number | null;
  categoryId: number | null;
  type: "income" | "expense" | "transfer" | null;
  dateFrom: string;
  dateTo: string;
}

interface TransactionFiltersProps {
  values: TransactionFilterValues;
  onChange: (values: TransactionFilterValues) => void;
  accounts: AccountOption[];
  categories: CategoryOption[];
}

/**
 * Filter bar for the transactions list.
 * Includes debounced search, dropdowns for account/category/type, and date range.
 */
export function TransactionFilters({
  values,
  onChange,
  accounts,
  categories,
}: TransactionFiltersProps) {
  const t = useTranslations("transactions");

  // Debounced search input
  const [searchInput, setSearchInput] = useState(values.search);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      if (searchInput !== values.search) {
        onChange({ ...values, search: searchInput });
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput]);

  const update = useCallback(
    (patch: Partial<TransactionFilterValues>) => {
      onChange({ ...values, ...patch });
    },
    [values, onChange],
  );

  const hasActiveFilters =
    values.search ||
    values.accountId ||
    values.categoryId ||
    values.type ||
    values.dateFrom ||
    values.dateTo;

  const clearFilters = () => {
    setSearchInput("");
    onChange({
      search: "",
      accountId: null,
      categoryId: null,
      type: null,
      dateFrom: "",
      dateTo: "",
    });
  };

  const typeOptions: { value: TransactionFilterValues["type"]; label: string }[] = [
    { value: null, label: t("allTypes") },
    { value: "income", label: t("income") },
    { value: "expense", label: t("expense") },
    { value: "transfer", label: t("transfer") },
  ];

  return (
    <div className="space-y-3">
      {/* Top row: search + type pills */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder={t("search")}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Type pills */}
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1">
          {typeOptions.map((opt) => (
            <button
              key={opt.value ?? "all"}
              onClick={() => update({ type: opt.value })}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                values.type === opt.value
                  ? "bg-white text-teal-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Second row: dropdowns + dates + clear */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Account dropdown */}
        <select
          value={values.accountId ?? ""}
          onChange={(e) =>
            update({ accountId: e.target.value ? Number(e.target.value) : null })
          }
          className="h-9 rounded-md border border-slate-200 bg-transparent px-3 text-sm text-slate-700 shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
        >
          <option value="">{t("allAccounts")}</option>
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>

        {/* Category dropdown */}
        <select
          value={values.categoryId ?? ""}
          onChange={(e) =>
            update({ categoryId: e.target.value ? Number(e.target.value) : null })
          }
          className="h-9 rounded-md border border-slate-200 bg-transparent px-3 text-sm text-slate-700 shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
        >
          <option value="">{t("allCategories")}</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        {/* Date from */}
        <div className="flex items-center gap-1.5">
          <label className="text-xs text-slate-500">{t("dateFrom")}</label>
          <Input
            type="date"
            value={values.dateFrom}
            onChange={(e) => update({ dateFrom: e.target.value })}
            className="w-36"
          />
        </div>

        {/* Date to */}
        <div className="flex items-center gap-1.5">
          <label className="text-xs text-slate-500">{t("dateTo")}</label>
          <Input
            type="date"
            value={values.dateTo}
            onChange={(e) => update({ dateTo: e.target.value })}
            className="w-36"
          />
        </div>

        {/* Clear filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="mr-1 h-3 w-3" />
            {t("clearFilters")}
          </Button>
        )}
      </div>
    </div>
  );
}
