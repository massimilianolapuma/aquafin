"use client";

import { useTranslations } from "next-intl";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface TransactionPaginationProps {
  page: number;
  totalPages: number;
  limit: number;
  total: number;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
}

const PAGE_SIZES = [10, 20, 50];

/**
 * Pagination controls with page navigation, current page indicator,
 * and a page-size selector.
 */
export function TransactionPagination({
  page,
  totalPages,
  limit,
  total,
  onPageChange,
  onLimitChange,
}: TransactionPaginationProps) {
  const t = useTranslations("transactions");

  return (
    <div className="flex flex-wrap items-center justify-between gap-4">
      {/* Showing X–Y of Z */}
      <p className="text-sm text-slate-500">
        {t("showing", {
          from: total === 0 ? 0 : (page - 1) * limit + 1,
          to: Math.min(page * limit, total),
          total,
        })}
      </p>

      <div className="flex items-center gap-4">
        {/* Page size selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">{t("perPage")}</span>
          <select
            value={limit}
            onChange={(e) => onLimitChange(Number(e.target.value))}
            className="h-8 rounded-md border border-slate-200 bg-transparent px-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
          >
            {PAGE_SIZES.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>

        {/* Page indicator */}
        <span className="text-sm text-slate-700">
          {t("page", { page, total: totalPages })}
        </span>

        {/* Prev / Next */}
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
