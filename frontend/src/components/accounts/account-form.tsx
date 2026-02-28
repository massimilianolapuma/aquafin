"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

import type { Account } from "./accounts-view";

/** Preset color palette for accounts */
const PRESET_COLORS = [
  "#0d9488", // teal-600
  "#2563eb", // blue-600
  "#7c3aed", // violet-600
  "#db2777", // pink-600
  "#ea580c", // orange-600
  "#16a34a", // green-600
  "#ca8a04", // yellow-600
  "#64748b", // slate-500
];

/** Available account types */
const ACCOUNT_TYPES = ["bank", "satispay", "paypal", "cash", "investment"] as const;
type AccountType = (typeof ACCOUNT_TYPES)[number];

interface AccountFormData {
  name: string;
  type: AccountType;
  currency: string;
  color: string;
  icon: string;
}

interface AccountFormProps {
  account: Account | null;
  onClose: () => void;
}

/**
 * Modal form for creating or editing an account.
 * Pre-fills values when editing an existing account.
 */
export function AccountForm({ account, onClose }: AccountFormProps) {
  const t = useTranslations("accounts");
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const isEditing = account !== null;

  const [formData, setFormData] = useState<AccountFormData>({
    name: account?.name ?? "",
    type: account?.type ?? "bank",
    currency: account?.currency ?? "EUR",
    color: account?.color ?? PRESET_COLORS[0],
    icon: account?.icon ?? "",
  });

  /** Update a single field */
  const setField = <K extends keyof AccountFormData>(
    key: K,
    value: AccountFormData[K],
  ) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const createMutation = useMutation({
    mutationFn: async (data: AccountFormData) => {
      const token = await getToken();
      return api.post<Account>("/accounts", data, {
        token: token ?? undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: AccountFormData) => {
      const token = await getToken();
      return api.put<Account>(`/accounts/${account!.id}`, data, {
        token: token ?? undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isEditing) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    /* Modal overlay */
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="relative w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
        >
          <X className="h-5 w-5" />
        </button>

        <h2 className="mb-6 text-lg font-semibold text-slate-900">
          {isEditing ? t("editAccount") : t("newAccount")}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Account name */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("accountName")}
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setField("name", e.target.value)}
              placeholder={t("accountName")}
              required
            />
          </div>

          {/* Account type */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("accountType")}
            </label>
            <select
              value={formData.type}
              onChange={(e) => setField("type", e.target.value as AccountType)}
              className="flex h-9 w-full rounded-md border border-slate-200 bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
            >
              {ACCOUNT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {t(type)}
                </option>
              ))}
            </select>
          </div>

          {/* Currency */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("currency")}
            </label>
            <Input
              value={formData.currency}
              onChange={(e) => setField("currency", e.target.value.toUpperCase())}
              placeholder="EUR"
              maxLength={3}
            />
          </div>

          {/* Color picker */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("color")}
            </label>
            <div className="flex flex-wrap gap-2">
              {PRESET_COLORS.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setField("color", color)}
                  className={`h-8 w-8 rounded-full border-2 transition-transform ${
                    formData.color === color
                      ? "scale-110 border-slate-900"
                      : "border-transparent hover:scale-105"
                  }`}
                  style={{ backgroundColor: color }}
                  title={color}
                />
              ))}
            </div>
          </div>

          {/* Icon */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              {t("icon")}
            </label>
            <Input
              value={formData.icon}
              onChange={(e) => setField("icon", e.target.value)}
              placeholder={t("iconPlaceholder")}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              {t("cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting || !formData.name}>
              {isSubmitting ? t("saving") : t("save")}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
