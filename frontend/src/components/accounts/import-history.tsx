"use client";

import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";

/** Shape of a single import record from the API */
interface ImportRecord {
  id: string;
  filename: string;
  file_type: string;
  source_type: string;
  status: string;
  row_count: number;
  imported_count: number;
  created_at: string;
}

interface ImportListResponse {
  items: ImportRecord[];
  total: number;
}

/** Status-to-color mapping */
const STATUS_COLORS: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-700",
  confirmed: "bg-emerald-100 text-emerald-700",
  error: "bg-red-100 text-red-700",
  failed: "bg-red-100 text-red-700",
  pending: "bg-yellow-100 text-yellow-700",
  preview_ready: "bg-blue-100 text-blue-700",
};

interface ImportHistoryProps {
  accountId: string;
}

/**
 * Displays the import history for a given account.
 * Shows file name, source type, status badge, row counts, and date.
 */
export function ImportHistory({ accountId }: ImportHistoryProps) {
  const t = useTranslations("accounts");
  const { getToken } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: ["imports", accountId],
    queryFn: async () => {
      const token = await getToken();
      return api.get<ImportListResponse>(
        `/imports?account_id=${accountId}`,
        { token: token ?? undefined },
      );
    },
  });

  const imports = data?.items ?? [];

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="h-12 animate-pulse rounded-lg bg-slate-100"
          />
        ))}
      </div>
    );
  }

  if (imports.length === 0) {
    return (
      <p className="py-2 text-center text-xs text-slate-400">
        {t("noImports")}
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {imports.map((imp) => {
        const statusClass =
          STATUS_COLORS[imp.status] ?? "bg-slate-100 text-slate-600";

        return (
          <div
            key={imp.id}
            className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-2 text-xs"
          >
            <FileText className="h-4 w-4 shrink-0 text-slate-400" />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-slate-700">
                {imp.filename}
              </p>
              <div className="flex items-center gap-2 text-slate-400">
                <span>{formatDate(imp.created_at)}</span>
                <span>·</span>
                <span>
                  {imp.imported_count}/{imp.row_count} {t("rowsImported")}
                </span>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-1.5">
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">
                {imp.source_type}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${statusClass}`}
              >
                {t(`status_${imp.status}` as Parameters<typeof t>[0])}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
