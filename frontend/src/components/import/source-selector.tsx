"use client";

import { useTranslations } from "next-intl";
import { Building, Smartphone, CreditCard } from "lucide-react";
import { cn } from "@/lib/utils";

/** Allowed source types matching the backend enum. */
export type SourceType = "bank" | "satispay" | "paypal";

interface SourceSelectorProps {
  /** Currently selected source, if any. */
  value: SourceType | null;
  /** Called when the user picks a source. */
  onChange: (source: SourceType | null) => void;
}

const SOURCES: { key: SourceType; icon: typeof Building; labelKey: string }[] =
  [
    { key: "bank", icon: Building, labelKey: "sourceBank" },
    { key: "satispay", icon: Smartphone, labelKey: "sourceSatispay" },
    { key: "paypal", icon: CreditCard, labelKey: "sourcePaypal" },
  ];

/** Row of clickable cards to select the import source (optional). */
export function SourceSelector({ value, onChange }: SourceSelectorProps) {
  const t = useTranslations("upload");

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-slate-700">
        {t("selectSource")}
      </p>
      <div className="grid grid-cols-3 gap-3">
        {SOURCES.map(({ key, icon: Icon, labelKey }) => {
          const selected = value === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onChange(selected ? null : key)}
              className={cn(
                "flex flex-col items-center gap-2 rounded-xl border p-4 text-sm font-medium transition-colors",
                selected
                  ? "border-teal-500 bg-teal-50 text-teal-700"
                  : "border-slate-200 bg-white text-slate-600 hover:border-teal-300 hover:bg-teal-50/30",
              )}
            >
              <Icon className="h-6 w-6" />
              {t(labelKey)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
