"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Upload, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Quick action buttons for common tasks. */
export function QuickActions() {
  const t = useTranslations("dashboard");

  return (
    <div className="flex flex-wrap gap-3">
      <Button variant="outline" asChild>
        <Link href="/import">
          <Upload className="mr-2 h-4 w-4" />
          {t("uploadFile")}
        </Link>
      </Button>
      <Button variant="outline" asChild>
        <Link href="/accounts">
          <Plus className="mr-2 h-4 w-4" />
          {t("newAccount")}
        </Link>
      </Button>
    </div>
  );
}
