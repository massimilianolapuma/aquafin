"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useTranslations } from "next-intl";
import { Upload, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadZoneProps {
  /** Currently selected file, if any. */
  file: File | null;
  /** Called when a file is selected or dropped. */
  onFileSelect: (file: File) => void;
}

/** Drag-and-drop zone for CSV / PDF file upload. */
export function UploadZone({ file, onFileSelect }: UploadZoneProps) {
  const t = useTranslations("upload");

  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) {
        onFileSelect(accepted[0]);
      }
    },
    [onFileSelect],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/pdf": [".pdf"],
    },
    maxSize: 10 * 1024 * 1024, // 10 MB
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors",
        isDragActive
          ? "border-teal-500 bg-teal-50"
          : file
            ? "border-teal-400 bg-teal-50/50"
            : "border-slate-300 bg-slate-50 hover:border-teal-400 hover:bg-teal-50/30",
      )}
    >
      <input {...getInputProps()} />

      {file ? (
        <>
          <FileText className="mb-3 h-10 w-10 text-teal-600" />
          <p className="text-sm font-medium text-teal-700">
            {t("fileSelected", { name: file.name })}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {t("acceptedFormats")}
          </p>
        </>
      ) : (
        <>
          <Upload className="mb-3 h-10 w-10 text-slate-400" />
          <p className="text-sm font-medium text-slate-700">
            {isDragActive ? t("dropzoneActive") : t("dropzone")}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {t("acceptedFormats")}
          </p>
        </>
      )}
    </div>
  );
}
