"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Search, Check, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import type { CategoryOption } from "./transactions-view";

interface CategoryEditPopoverProps {
  /** Currently assigned category id (null = uncategorized) */
  currentCategoryId: number | null;
  categories: CategoryOption[];
  /** Fires when the user confirms a category change */
  onConfirm: (categoryId: number, applyToSimilar: boolean) => void;
  onClose: () => void;
}

/**
 * Inline popover to reassign a transaction's category.
 * Anchored to the category badge in the table.
 */
export function CategoryEditPopover({
  currentCategoryId,
  categories,
  onConfirm,
  onClose,
}: CategoryEditPopoverProps) {
  const t = useTranslations("transactions");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<number | null>(currentCategoryId);
  const [applyToSimilar, setApplyToSimilar] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  const filtered = useMemo(
    () =>
      categories.filter((c) =>
        c.name.toLowerCase().includes(search.toLowerCase()),
      ),
    [categories, search],
  );

  return (
    <div
      ref={popoverRef}
      className="absolute right-0 top-full z-50 mt-1 w-64 rounded-lg border border-slate-200 bg-white p-3 shadow-lg"
    >
      {/* Header */}
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium">{t("editCategory")}</span>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-2">
        <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder={t("search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 pl-7 text-xs"
        />
      </div>

      {/* Category list */}
      <ul className="max-h-40 overflow-y-auto">
        {filtered.map((cat) => (
          <li key={cat.id}>
            <button
              onClick={() => setSelected(cat.id)}
              className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
                selected === cat.id
                  ? "bg-teal-50 text-teal-700"
                  : "text-slate-700 hover:bg-slate-50"
              }`}
            >
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: cat.color }}
              />
              <span className="flex-1">{cat.name}</span>
              {selected === cat.id && <Check className="h-3.5 w-3.5" />}
            </button>
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="px-2 py-3 text-center text-xs text-slate-400">
            {t("noTransactions")}
          </li>
        )}
      </ul>

      {/* Apply to similar */}
      <label className="mt-2 flex items-center gap-2 text-xs text-slate-600">
        <input
          type="checkbox"
          checked={applyToSimilar}
          onChange={(e) => setApplyToSimilar(e.target.checked)}
          className="rounded border-slate-300"
        />
        {t("applyToSimilar")}
      </label>

      {/* Actions */}
      <div className="mt-3 flex items-center justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={onClose}>
          {t("cancelAction")}
        </Button>
        <Button
          size="sm"
          disabled={selected === null || selected === currentCategoryId}
          onClick={() => {
            if (selected !== null) onConfirm(selected, applyToSimilar);
          }}
        >
          {t("confirmAction")}
        </Button>
      </div>
    </div>
  );
}
