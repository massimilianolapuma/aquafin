"use client";

import { useState, useCallback, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeftRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";

import { TransactionFilters, type TransactionFilterValues } from "./transaction-filters";
import { TransactionsTable } from "./transactions-table";
import { TransactionPagination } from "./transaction-pagination";

/** Shape of a single transaction returned by the API */
export interface Transaction {
  id: number;
  account_id: number | null;
  category_id: number | null;
  import_id: number | null;
  amount: number;
  currency: string;
  date: string;
  description: string;
  original_description: string | null;
  type: "income" | "expense" | "transfer";
  categorization_method: string | null;
  is_recurring: boolean;
  tags: string[] | null;
  metadata_extra: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/** Paginated response wrapper */
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

/** Account option for the filter dropdown */
export interface AccountOption {
  id: number;
  name: string;
}

/** Mock category used until the categories API is ready */
export interface CategoryOption {
  id: number;
  name: string;
  color: string;
}

/** Hardcoded mock categories for MVP */
export const MOCK_CATEGORIES: CategoryOption[] = [
  { id: 1, name: "Alimentari", color: "#4CAF50" },
  { id: 2, name: "Casa", color: "#2196F3" },
  { id: 3, name: "Trasporti", color: "#FF9800" },
  { id: 4, name: "Svago", color: "#E91E63" },
  { id: 5, name: "Servizi", color: "#00BCD4" },
  { id: 6, name: "Salute", color: "#F44336" },
  { id: 7, name: "Shopping", color: "#9C27B0" },
  { id: 8, name: "Stipendio", color: "#4CAF50" },
  { id: 9, name: "Utenze", color: "#607D8B" },
  { id: 10, name: "Abbonamenti", color: "#795548" },
  { id: 11, name: "Altro", color: "#9E9E9E" },
];

/**
 * Main transactions page component.
 * Renders filters, table with inline category editing, pagination, and bulk actions.
 */
export function TransactionsView() {
  const t = useTranslations("transactions");
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  // --- filter state ---
  const [filters, setFilters] = useState<TransactionFilterValues>({
    search: "",
    accountId: null,
    categoryId: null,
    type: null,
    dateFrom: "",
    dateTo: "",
  });

  // --- pagination state ---
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);

  // --- selection state ---
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
    setSelectedIds(new Set());
  }, [filters]);

  // --- build query params ---
  const buildParams = useCallback(() => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("limit", String(limit));
    if (filters.search) params.set("search", filters.search);
    if (filters.accountId) params.set("account_id", String(filters.accountId));
    if (filters.categoryId) params.set("category_id", String(filters.categoryId));
    if (filters.type) params.set("type", filters.type);
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    return params.toString();
  }, [page, limit, filters]);

  // --- fetch transactions ---
  const {
    data: txData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["transactions", page, limit, filters],
    queryFn: async () => {
      const token = await getToken();
      return api.get<PaginatedResponse<Transaction>>(
        `/transactions?${buildParams()}`,
        { token: token ?? undefined },
      );
    },
  });

  // --- fetch accounts for filter dropdown ---
  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: async () => {
      const token = await getToken();
      return api.get<{ items: AccountOption[]; total: number }>("/accounts", {
        token: token ?? undefined,
      });
    },
  });

  const accounts: AccountOption[] = accountsData?.items ?? [];
  const transactions = txData?.items ?? [];
  const total = txData?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  // --- mutations ---
  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ["transactions"] });

  /** Update a single transaction's category (optionally apply to similar) */
  const recategorizeMutation = useMutation({
    mutationFn: async ({
      transactionId,
      categoryId,
      applyToSimilar,
    }: {
      transactionId: number;
      categoryId: number;
      applyToSimilar: boolean;
    }) => {
      const token = await getToken();
      return api.post(
        `/transactions/${transactionId}/recategorize`,
        { category_id: categoryId, apply_to_similar: applyToSimilar },
        { token: token ?? undefined },
      );
    },
    onSuccess: () => invalidate(),
  });

  /** Bulk-categorize selected transactions */
  const bulkCategorizeMutation = useMutation({
    mutationFn: async ({
      transactionIds,
      categoryId,
    }: {
      transactionIds: number[];
      categoryId: number;
    }) => {
      const token = await getToken();
      return api.post(
        "/transactions/bulk-categorize",
        { transaction_ids: transactionIds, category_id: categoryId },
        { token: token ?? undefined },
      );
    },
    onSuccess: () => {
      setSelectedIds(new Set());
      invalidate();
    },
  });

  /** Delete a single transaction */
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const token = await getToken();
      return api.del(`/transactions/${id}`, { token: token ?? undefined });
    },
    onSuccess: () => {
      invalidate();
    },
  });

  // --- selection helpers ---
  const handleToggleSelect = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleToggleAll = useCallback(() => {
    if (selectedIds.size === transactions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(transactions.map((tx) => tx.id)));
    }
  }, [selectedIds.size, transactions]);

  const handleBulkCategorize = useCallback(
    (categoryId: number) => {
      bulkCategorizeMutation.mutate({
        transactionIds: Array.from(selectedIds),
        categoryId,
      });
    },
    [selectedIds, bulkCategorizeMutation],
  );

  const handleBulkDelete = useCallback(() => {
    for (const id of selectedIds) {
      deleteMutation.mutate(id);
    }
    setSelectedIds(new Set());
  }, [selectedIds, deleteMutation]);

  // --- skeleton rows for loading state ---
  const skeletonRows = Array.from({ length: limit }, (_, i) => i);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-100 text-teal-600">
          <ArrowLeftRight className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-slate-500">
            {t("subtitle", { count: total })}
          </p>
        </div>
      </div>

      {/* Filters */}
      <TransactionFilters
        values={filters}
        onChange={setFilters}
        accounts={accounts}
        categories={MOCK_CATEGORIES}
      />

      {/* Table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{t("title")}</CardTitle>
          <CardDescription>
            {t("showing", {
              from: total === 0 ? 0 : (page - 1) * limit + 1,
              to: Math.min(page * limit, total),
              total,
            })}
          </CardDescription>
        </CardHeader>
        <CardContent className="px-0 pb-0">
          {isLoading ? (
            <div className="divide-y divide-slate-100">
              {skeletonRows.map((i) => (
                <div key={i} className="flex items-center gap-4 px-6 py-3">
                  <div className="h-4 w-4 animate-pulse rounded bg-slate-200" />
                  <div className="h-4 w-20 animate-pulse rounded bg-slate-200" />
                  <div className="h-4 flex-1 animate-pulse rounded bg-slate-200" />
                  <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
                  <div className="h-4 w-20 animate-pulse rounded bg-slate-200" />
                  <div className="h-6 w-16 animate-pulse rounded-full bg-slate-200" />
                </div>
              ))}
            </div>
          ) : isError ? (
            <div className="px-6 py-12 text-center text-sm text-red-500">
              {t("error")}
            </div>
          ) : transactions.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="text-sm font-medium text-slate-900">
                {t("noTransactions")}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {t("noTransactionsHint")}
              </p>
            </div>
          ) : (
            <TransactionsTable
              transactions={transactions}
              categories={MOCK_CATEGORIES}
              accounts={accounts}
              selectedIds={selectedIds}
              onToggleSelect={handleToggleSelect}
              onToggleAll={handleToggleAll}
              onRecategorize={(txId, catId, applyToSimilar) =>
                recategorizeMutation.mutate({
                  transactionId: txId,
                  categoryId: catId,
                  applyToSimilar,
                })
              }
              onBulkCategorize={handleBulkCategorize}
              onBulkDelete={handleBulkDelete}
            />
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > 0 && (
        <TransactionPagination
          page={page}
          totalPages={totalPages}
          limit={limit}
          total={total}
          onPageChange={setPage}
          onLimitChange={(newLimit) => {
            setLimit(newLimit);
            setPage(1);
          }}
        />
      )}
    </div>
  );
}
