"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { COLOR_PRESETS, type Category } from "@/lib/mock-categories";

interface CategoryFormProps {
  /** Existing category to edit, or undefined for create. */
  category?: Category;
  /** Available parent categories (for the dropdown). */
  categories: Category[];
  /** Called with the new/updated category on save. */
  onSave: (category: Category) => void;
  /** Called when the user cancels. */
  onCancel: () => void;
}

/**
 * Inline form for creating or editing a custom category.
 * Features: name, emoji icon, color grid, parent dropdown, type toggle.
 */
export function CategoryForm({
  category,
  categories,
  onSave,
  onCancel,
}: CategoryFormProps) {
  const t = useTranslations("categories");

  const [name, setName] = useState(category?.name ?? "");
  const [icon, setIcon] = useState(category?.icon ?? "📁");
  const [color, setColor] = useState(category?.color ?? COLOR_PRESETS[0]);
  const [parentId, setParentId] = useState<string | null>(category?.parentId ?? null);
  const [type, setType] = useState<"expense" | "income">(category?.type ?? "expense");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const saved: Category = {
      id: category?.id ?? `cust-${Date.now()}`,
      name: name.trim(),
      icon,
      color,
      type,
      parentId,
      isSystem: false,
      transactionCount: category?.transactionCount ?? 0,
      totalAmount: category?.totalAmount ?? 0,
    };
    onSave(saved);
  };

  // Only show parent categories of the same type
  const parentOptions = categories.filter((c) => c.type === type && c.id !== category?.id);

  return (
    <Card className="border-teal-200 bg-teal-50/30">
      <CardHeader className="pb-4">
        <CardTitle className="text-base">
          {category ? t("editCategory") : t("addCategory")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("categoryName")}
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("categoryName")}
              required
            />
          </div>

          {/* Icon */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("categoryIcon")}
            </label>
            <Input
              value={icon}
              onChange={(e) => setIcon(e.target.value)}
              className="w-20 text-center text-lg"
              maxLength={4}
            />
          </div>

          {/* Color */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("categoryColor")}
            </label>
            <div className="flex flex-wrap gap-2">
              {COLOR_PRESETS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  className={`h-8 w-8 rounded-full border-2 transition-transform ${
                    color === c
                      ? "border-slate-900 scale-110"
                      : "border-transparent hover:scale-105"
                  }`}
                  style={{ backgroundColor: c }}
                  title={c}
                />
              ))}
            </div>
          </div>

          {/* Type toggle */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("categoryType")}
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setType("expense");
                  setParentId(null);
                }}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  type === "expense"
                    ? "bg-rose-100 text-rose-700 ring-1 ring-rose-300"
                    : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                }`}
              >
                {t("expenseType")}
              </button>
              <button
                type="button"
                onClick={() => {
                  setType("income");
                  setParentId(null);
                }}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  type === "income"
                    ? "bg-emerald-100 text-emerald-700 ring-1 ring-emerald-300"
                    : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                }`}
              >
                {t("incomeType")}
              </button>
            </div>
          </div>

          {/* Parent category dropdown */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("categoryParent")}
            </label>
            <select
              value={parentId ?? ""}
              onChange={(e) => setParentId(e.target.value || null)}
              className="flex h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
            >
              <option value="">{t("noParent")}</option>
              {parentOptions.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.icon} {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <Button type="submit" size="sm">
              {t("save")}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={onCancel}>
              {t("cancel")}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
