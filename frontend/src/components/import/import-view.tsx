"use client";

import { useState, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { AlertCircle } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

import { UploadZone } from "@/components/import/upload-zone";
import {
  SourceSelector,
  type SourceType,
} from "@/components/import/source-selector";
import {
  AccountSelector,
  MOCK_ACCOUNTS,
  type AccountOption,
} from "@/components/import/account-selector";
import { UploadProgress } from "@/components/import/upload-progress";
import {
  PreviewTable,
  type PreviewTransaction,
} from "@/components/import/preview-table";
import { ImportSummary } from "@/components/import/import-summary";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type FlowState =
  | "upload"
  | "uploading"
  | "preview"
  | "confirming"
  | "success"
  | "error";

interface UploadResponse {
  id: string;
  filename: string;
  file_type: string;
  source_type: string;
  status: string;
  row_count: number;
  created_at: string;
  preview: {
    transactions: PreviewTransaction[];
    errors: string[];
  };
}

interface ConfirmResponse {
  import_id: string;
  status: string;
  imported_count: number;
  categorized_count: number;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/** Main client component orchestrating the full import flow. */
export function ImportView() {
  const t = useTranslations("upload");
  const { getToken } = useAuth();

  // Flow state
  const [state, setState] = useState<FlowState>("upload");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Upload form
  const [file, setFile] = useState<File | null>(null);
  const [source, setSource] = useState<SourceType | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);

  // Accounts – use mock data for MVP; swap to API call later
  const [accounts] = useState<AccountOption[]>(MOCK_ACCOUNTS);

  // Preview data
  const [importId, setImportId] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<PreviewTransaction[]>([]);
  const [parseErrors, setParseErrors] = useState<string[]>([]);
  const [categoryOverrides, setCategoryOverrides] = useState<
    Record<string, string>
  >({});

  // Success data
  const [importedCount, setImportedCount] = useState(0);
  const [categorizedCount, setCategorizedCount] = useState(0);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleCategoryOverride = useCallback(
    (tempId: string, category: string) => {
      setCategoryOverrides((prev) => ({ ...prev, [tempId]: category }));
    },
    [],
  );

  /** Upload the file to the backend. */
  const handleUpload = useCallback(async () => {
    if (!file || !accountId) return;

    setState("uploading");
    setErrorMessage(null);

    try {
      const token = await getToken();
      const formData = new FormData();
      formData.append("file", file);
      formData.append("account_id", accountId);
      if (source) formData.append("source_type", source);

      const res = await api.upload<UploadResponse>("/imports/upload", formData, {
        token: token ?? undefined,
      });

      setImportId(res.id);
      setTransactions(res.preview.transactions);
      setParseErrors(res.preview.errors);
      setCategoryOverrides({});
      setState("preview");
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : t("errorTitle"),
      );
      setState("error");
    }
  }, [file, accountId, source, getToken, t]);

  /** Confirm the import (with optional category overrides). */
  const handleConfirm = useCallback(async () => {
    if (!importId) return;

    setState("confirming");
    setErrorMessage(null);

    try {
      const token = await getToken();
      const body: { category_overrides?: Record<string, string> } = {};
      if (Object.keys(categoryOverrides).length > 0) {
        body.category_overrides = categoryOverrides;
      }

      const res = await api.post<ConfirmResponse>(
        `/imports/${importId}/confirm`,
        body,
        { token: token ?? undefined },
      );

      setImportedCount(res.imported_count);
      setCategorizedCount(res.categorized_count);
      setState("success");
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : t("errorTitle"),
      );
      setState("error");
    }
  }, [importId, categoryOverrides, getToken, t]);

  /** Cancel / delete the pending import and return to upload. */
  const handleCancel = useCallback(async () => {
    if (importId) {
      try {
        const token = await getToken();
        await api.del(`/imports/${importId}`, {
          token: token ?? undefined,
        });
      } catch {
        // best-effort deletion – ignore errors
      }
    }
    // Reset all state
    setImportId(null);
    setTransactions([]);
    setParseErrors([]);
    setCategoryOverrides({});
    setFile(null);
    setSource(null);
    setAccountId(null);
    setErrorMessage(null);
    setState("upload");
  }, [importId, getToken]);

  /** Retry from the upload step. */
  const handleRetry = useCallback(() => {
    setErrorMessage(null);
    setState("upload");
  }, []);

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const canUpload = !!file && !!accountId;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
        <p className="text-sm text-slate-500">{t("subtitle")}</p>
      </div>

      <Card>
        {/* ── STATE: upload ─────────────────────────────────── */}
        {state === "upload" && (
          <>
            <CardContent className="space-y-6 pt-6">
              <UploadZone file={file} onFileSelect={setFile} />
              <SourceSelector value={source} onChange={setSource} />
              <AccountSelector
                accounts={accounts}
                value={accountId}
                onChange={setAccountId}
              />
            </CardContent>
            <CardFooter className="justify-end gap-3">
              <Button disabled={!canUpload} onClick={handleUpload}>
                {t("uploadButton")}
              </Button>
            </CardFooter>
          </>
        )}

        {/* ── STATE: uploading ─────────────────────────────── */}
        {state === "uploading" && (
          <CardContent className="pt-6">
            <UploadProgress fileName={file?.name ?? ""} />
          </CardContent>
        )}

        {/* ── STATE: preview ───────────────────────────────── */}
        {state === "preview" && (
          <>
            <CardHeader>
              <CardTitle>{t("previewTitle")}</CardTitle>
              <CardDescription>
                {t("previewSubtitle", { count: transactions.length })}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PreviewTable
                transactions={transactions}
                errors={parseErrors}
                categoryOverrides={categoryOverrides}
                onCategoryOverride={handleCategoryOverride}
              />
            </CardContent>
            <CardFooter className="justify-end gap-3">
              <Button variant="outline" onClick={handleCancel}>
                {t("cancelImport")}
              </Button>
              <Button onClick={handleConfirm}>{t("confirmAll")}</Button>
            </CardFooter>
          </>
        )}

        {/* ── STATE: confirming ────────────────────────────── */}
        {state === "confirming" && (
          <CardContent className="pt-6">
            <UploadProgress fileName={file?.name ?? ""} />
          </CardContent>
        )}

        {/* ── STATE: success ───────────────────────────────── */}
        {state === "success" && (
          <CardContent className="pt-6">
            <ImportSummary
              importedCount={importedCount}
              categorizedCount={categorizedCount}
            />
          </CardContent>
        )}

        {/* ── STATE: error ─────────────────────────────────── */}
        {state === "error" && (
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4 py-12">
              <AlertCircle className="h-12 w-12 text-rose-500" />
              <h2 className="text-lg font-semibold text-slate-900">
                {t("errorTitle")}
              </h2>
              {errorMessage && (
                <p className="text-sm text-slate-600">{errorMessage}</p>
              )}
              <Button variant="outline" onClick={handleRetry}>
                {t("errorRetry")}
              </Button>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
