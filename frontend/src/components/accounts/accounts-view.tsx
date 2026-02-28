"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { Landmark, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

import { AccountCard } from "./account-card";
import { AccountForm } from "./account-form";

/** Shape of an account returned by the API */
export interface Account {
  id: string;
  user_id: string;
  name: string;
  type: "bank" | "satispay" | "paypal" | "cash" | "investment";
  currency: string;
  color: string | null;
  icon: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AccountListResponse {
  items: Account[];
  total: number;
}

/**
 * Main accounts page component.
 * Displays a grid of account cards with create/edit/delete functionality.
 */
export function AccountsView() {
  const t = useTranslations("accounts");
  const { getToken } = useAuth();
  const [formOpen, setFormOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["accounts"],
    queryFn: async () => {
      const token = await getToken();
      return api.get<AccountListResponse>("/accounts", {
        token: token ?? undefined,
      });
    },
  });

  const accounts = data?.items ?? [];

  /** Open form in create mode */
  const handleCreate = () => {
    setEditingAccount(null);
    setFormOpen(true);
  };

  /** Open form in edit mode */
  const handleEdit = (account: Account) => {
    setEditingAccount(account);
    setFormOpen(true);
  };

  /** Close form */
  const handleCloseForm = () => {
    setFormOpen(false);
    setEditingAccount(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
          <p className="text-sm text-slate-500">{t("subtitle")}</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          {t("newAccount")}
        </Button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="h-40 p-6" />
            </Card>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6 text-center text-red-600">
            {t("error")}
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!isLoading && !error && accounts.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Landmark className="mb-4 h-12 w-12 text-slate-300" />
            <p className="text-lg font-medium text-slate-600">
              {t("noAccounts")}
            </p>
            <p className="mb-4 text-sm text-slate-400">
              {t("noAccountsHint")}
            </p>
            <Button onClick={handleCreate}>
              <Plus className="mr-2 h-4 w-4" />
              {t("newAccount")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Accounts grid */}
      {!isLoading && !error && accounts.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      {/* Create / Edit form modal */}
      {formOpen && (
        <AccountForm
          account={editingAccount}
          onClose={handleCloseForm}
        />
      )}
    </div>
  );
}
