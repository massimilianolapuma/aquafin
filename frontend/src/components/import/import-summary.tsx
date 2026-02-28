"use client";

import { useTranslations } from "next-intl";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface ImportSummaryProps {
  importedCount: number;
  categorizedCount: number;
}

/** Success screen shown after a confirmed import. */
export function ImportSummary({
  importedCount,
  categorizedCount,
}: ImportSummaryProps) {
  const t = useTranslations("upload");
  const router = useRouter();

  return (
    <div className="flex flex-col items-center gap-5 py-12">
      <CheckCircle2 className="h-16 w-16 animate-bounce text-emerald-500" />
      <h2 className="text-xl font-bold text-slate-900">
        {t("successTitle")}
      </h2>
      <div className="space-y-1 text-center text-sm text-slate-600">
        <p>{t("successImported", { count: importedCount })}</p>
        <p>{t("successCategorized", { count: categorizedCount })}</p>
      </div>
      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          onClick={() => router.push("/transactions")}
        >
          {t("goToTransactions")}
        </Button>
        <Button onClick={() => router.refresh()}>
          {t("importAnother")}
        </Button>
      </div>
    </div>
  );
}
