"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

/** Minimal account shape for the selector. */
export interface AccountOption {
  id: string;
  name: string;
  type: string;
}

interface AccountSelectorProps {
  accounts: AccountOption[];
  value: string | null;
  onChange: (accountId: string) => void;
  isLoading?: boolean;
}

/** Mock accounts used until the API is available. */
export const MOCK_ACCOUNTS: AccountOption[] = [
  { id: "acc-1", name: "Conto Principale", type: "bank" },
  { id: "acc-2", name: "Satispay", type: "satispay" },
  { id: "acc-3", name: "PayPal", type: "paypal" },
  { id: "acc-4", name: "Contanti", type: "cash" },
];

/** Dropdown to pick the target account for the import. */
export function AccountSelector({
  accounts,
  value,
  onChange,
  isLoading,
}: AccountSelectorProps) {
  const t = useTranslations("upload");

  return (
    <div className="space-y-2">
      <label
        htmlFor="account-select"
        className="text-sm font-medium text-slate-700"
      >
        {t("selectAccount")}
      </label>
      <select
        id="account-select"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={isLoading}
        className={cn(
          "flex h-9 w-full rounded-md border border-slate-200 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        <option value="" disabled>
          {isLoading ? t("selectAccount") + "..." : t("selectAccount")}
        </option>
        {accounts.map((acc) => (
          <option key={acc.id} value={acc.id}>
            {acc.name} ({acc.type})
          </option>
        ))}
      </select>
    </div>
  );
}
