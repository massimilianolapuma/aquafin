"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Wallet,
  Building2,
  CreditCard,
  Banknote,
  TrendingUp,
  Edit,
  Trash2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

import type { Account } from "./accounts-view";
import { ImportHistory } from "./import-history";

/** Map account types to their respective icons */
const ACCOUNT_ICONS: Record<Account["type"], React.ElementType> = {
  bank: Building2,
  satispay: Wallet,
  paypal: CreditCard,
  cash: Banknote,
  investment: TrendingUp,
};

/** Map account types to translated label keys */
const ACCOUNT_TYPE_KEYS: Record<Account["type"], string> = {
  bank: "bank",
  satispay: "satispay",
  paypal: "paypal",
  cash: "cash",
  investment: "investment",
};

interface AccountCardProps {
  account: Account;
  onEdit: (account: Account) => void;
}

/**
 * Card representing a single financial account.
 * Shows name, type badge, currency, color accent, and action buttons.
 * Expands to reveal import history.
 */
export function AccountCard({ account, onEdit }: AccountCardProps) {
  const t = useTranslations("accounts");
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [expanded, setExpanded] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const Icon = ACCOUNT_ICONS[account.type] ?? Wallet;
  const borderColor = account.color ?? "#0d9488"; // teal-600 default

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      return api.del<void>(`/accounts/${account.id}`, {
        token: token ?? undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    },
  });

  const handleDelete = () => {
    if (confirmDelete) {
      deleteMutation.mutate();
    } else {
      setConfirmDelete(true);
    }
  };

  return (
    <Card
      className="relative overflow-hidden transition-shadow hover:shadow-md"
      style={{ borderLeftWidth: "4px", borderLeftColor: borderColor }}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg"
            style={{ backgroundColor: `${borderColor}15` }}
          >
            <Icon className="h-5 w-5" style={{ color: borderColor }} />
          </div>
          <div>
            <CardTitle className="text-base">{account.name}</CardTitle>
            <span className="inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
              {t(ACCOUNT_TYPE_KEYS[account.type])}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onEdit(account)}
            title={t("editAccount")}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            title={confirmDelete ? t("confirmDelete") : t("deleteAccount")}
            className={confirmDelete ? "text-red-600 hover:text-red-700" : ""}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Currency badge */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">{t("currency")}</span>
          <span className="text-sm font-medium text-slate-700">
            {account.currency}
          </span>
        </div>

        {/* Active / Inactive status */}
        {!account.is_active && (
          <span className="inline-block rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-500">
            {t("inactive")}
          </span>
        )}

        {/* Toggle import history */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-between text-xs"
          onClick={() => setExpanded((prev) => !prev)}
        >
          {t("importHistory")}
          {expanded ? (
            <ChevronUp className="ml-1 h-3 w-3" />
          ) : (
            <ChevronDown className="ml-1 h-3 w-3" />
          )}
        </Button>

        {expanded && <ImportHistory accountId={account.id} />}
      </CardContent>
    </Card>
  );
}
