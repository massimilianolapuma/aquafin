"use client";

import { useState, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import {
  Download,
  FileSpreadsheet,
  FileJson,
  Shield,
  Loader2,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

/** Account option for the filter dropdown */
interface AccountOption {
  id: string;
  name: string;
}

interface AccountListResponse {
  items: AccountOption[];
  total: number;
}

/** Current filter state */
interface ExportFilters {
  account_id: string;
  category: string;
  date_from: string;
  date_to: string;
  type: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

/**
 * Export page component.
 * Provides filter controls and download buttons for CSV, JSON, and GDPR exports.
 */
export function ExportView() {
  const t = useTranslations("export");
  const { getToken } = useAuth();

  const [filters, setFilters] = useState<ExportFilters>({
    account_id: "",
    category: "",
    date_from: "",
    date_to: "",
    type: "",
  });

  const [downloadingCsv, setDownloadingCsv] = useState(false);
  const [downloadingJson, setDownloadingJson] = useState(false);
  const [downloadingGdpr, setDownloadingGdpr] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  /** Fetch accounts for the filter dropdown */
  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: async () => {
      const token = await getToken();
      return api.get<AccountListResponse>("/accounts", {
        token: token ?? undefined,
      });
    },
  });

  const accounts = accountsData?.items ?? [];

  /** Update a single filter field */
  const setFilter = <K extends keyof ExportFilters>(
    key: K,
    value: ExportFilters[K],
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  /** Build query string from current filters */
  const buildQueryString = useCallback((): string => {
    const params = new URLSearchParams();
    if (filters.account_id) params.set("account_id", filters.account_id);
    if (filters.category) params.set("category_id", filters.category);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (filters.type) params.set("type", filters.type);
    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }, [filters]);

  /** Generic blob download helper */
  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  /** Download CSV export */
  const handleDownloadCsv = async () => {
    setDownloadingCsv(true);
    setMessage(null);
    try {
      const token = await getToken();
      const qs = buildQueryString();
      const response = await fetch(`${API_BASE}/exports/csv${qs}`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!response.ok) throw new Error("Export failed");
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition");
      const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
      const filename = filenameMatch?.[1] ?? "aquafin_export.csv";
      downloadBlob(blob, filename);
      setMessage({ type: "success", text: t("downloadSuccess") });
    } catch {
      setMessage({ type: "error", text: t("downloadError") });
    } finally {
      setDownloadingCsv(false);
    }
  };

  /** Download JSON export */
  const handleDownloadJson = async () => {
    setDownloadingJson(true);
    setMessage(null);
    try {
      const token = await getToken();
      const qs = buildQueryString();
      const response = await fetch(`${API_BASE}/exports/json${qs}`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!response.ok) throw new Error("Export failed");
      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadBlob(blob, `aquafin_export_${timestamp}.json`);
      setMessage({ type: "success", text: t("downloadSuccess") });
    } catch {
      setMessage({ type: "error", text: t("downloadError") });
    } finally {
      setDownloadingJson(false);
    }
  };

  /** Download GDPR export (all user data) */
  const handleDownloadGdpr = async () => {
    setDownloadingGdpr(true);
    setMessage(null);
    try {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/exports/gdpr`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!response.ok) throw new Error("GDPR export failed");
      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      downloadBlob(blob, `aquafin_gdpr_export_${timestamp}.json`);
      setMessage({ type: "success", text: t("downloadSuccess") });
    } catch {
      setMessage({ type: "error", text: t("downloadError") });
    } finally {
      setDownloadingGdpr(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
        <p className="text-sm text-slate-500">{t("subtitle")}</p>
      </div>

      {/* Feedback message */}
      {message && (
        <div
          className={`rounded-lg px-4 py-3 text-sm ${
            message.type === "success"
              ? "bg-emerald-50 text-emerald-700"
              : "bg-red-50 text-red-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Filters Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("filtersTitle")}</CardTitle>
          <CardDescription>{t("filtersDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Account filter */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                {t("accountFilter")}
              </label>
              <select
                value={filters.account_id}
                onChange={(e) => setFilter("account_id", e.target.value)}
                className="flex h-9 w-full rounded-md border border-slate-200 bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
              >
                <option value="">{t("allAccounts")}</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category filter */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                {t("categoryFilter")}
              </label>
              <Input
                value={filters.category}
                onChange={(e) => setFilter("category", e.target.value)}
                placeholder={t("categoryPlaceholder")}
              />
            </div>

            {/* Type filter */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                {t("typeFilter")}
              </label>
              <select
                value={filters.type}
                onChange={(e) => setFilter("type", e.target.value)}
                className="flex h-9 w-full rounded-md border border-slate-200 bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
              >
                <option value="">{t("allTypes")}</option>
                <option value="income">{t("income")}</option>
                <option value="expense">{t("expense")}</option>
              </select>
            </div>

            {/* Date from */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                {t("dateFrom")}
              </label>
              <Input
                type="date"
                value={filters.date_from}
                onChange={(e) => setFilter("date_from", e.target.value)}
              />
            </div>

            {/* Date to */}
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">
                {t("dateTo")}
              </label>
              <Input
                type="date"
                value={filters.date_to}
                onChange={(e) => setFilter("date_to", e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Download Buttons Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("downloadTitle")}</CardTitle>
          <CardDescription>{t("downloadDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={handleDownloadCsv}
              disabled={downloadingCsv}
              className="gap-2"
            >
              {downloadingCsv ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="h-4 w-4" />
              )}
              {downloadingCsv ? t("downloading") : t("downloadCsv")}
            </Button>

            <Button
              onClick={handleDownloadJson}
              disabled={downloadingJson}
              variant="outline"
              className="gap-2"
            >
              {downloadingJson ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileJson className="h-4 w-4" />
              )}
              {downloadingJson ? t("downloading") : t("downloadJson")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* GDPR Export Card */}
      <Card className="border-slate-300">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-slate-500" />
            <CardTitle className="text-base">{t("gdprTitle")}</CardTitle>
          </div>
          <CardDescription>{t("gdprDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleDownloadGdpr}
            disabled={downloadingGdpr}
            variant="secondary"
            className="gap-2"
          >
            {downloadingGdpr ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            {downloadingGdpr ? t("gdprExporting") : t("gdprExport")}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
