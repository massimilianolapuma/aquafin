"use client";

import { useTranslations } from "next-intl";
import { Loader2 } from "lucide-react";

interface UploadProgressProps {
  /** Name of the file being uploaded. */
  fileName: string;
}

/** Animated spinner shown while the file is being uploaded and parsed. */
export function UploadProgress({ fileName }: UploadProgressProps) {
  const t = useTranslations("upload");

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <Loader2 className="h-10 w-10 animate-spin text-teal-600" />
      <p className="text-sm font-medium text-slate-700">{t("uploading")}</p>
      <p className="text-xs text-slate-500">{fileName}</p>
    </div>
  );
}
