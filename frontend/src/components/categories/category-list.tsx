"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import {
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  Shield,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/format";
import {
  MOCK_CATEGORIES,
  type Category,
} from "@/lib/mock-categories";
import { CategoryForm } from "./category-form";

/**
 * Hierarchical category display grouped by type (expenses / income).
 * System categories are read-only; custom categories support edit & delete.
 */
export function CategoryList() {
  const t = useTranslations("categories");
  const [categories, setCategories] = useState<Category[]>(MOCK_CATEGORIES);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Build parent→children map
  const parents = categories.filter((c) => c.parentId === null);
  const childrenOf = (parentId: string) =>
    categories.filter((c) => c.parentId === parentId);

  const expenseParents = parents.filter((c) => c.type === "expense");
  const incomeParents = parents.filter((c) => c.type === "income");

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleDelete = (id: string) => {
    if (!window.confirm(t("confirmDelete"))) return;
    setCategories((prev) => prev.filter((c) => c.id !== id && c.parentId !== id));
  };

  const handleSave = (category: Category) => {
    setCategories((prev) => {
      const exists = prev.find((c) => c.id === category.id);
      if (exists) {
        return prev.map((c) => (c.id === category.id ? category : c));
      }
      return [...prev, category];
    });
    setEditingCategory(null);
    setIsCreating(false);
  };

  const handleCancel = () => {
    setEditingCategory(null);
    setIsCreating(false);
  };

  /** Render a single category row. */
  const renderCategory = (cat: Category, isChild = false) => {
    const children = childrenOf(cat.id);
    const hasChildren = children.length > 0;
    const isExpanded = expandedIds.has(cat.id);

    return (
      <div key={cat.id}>
        <div
          className={`flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors ${
            isChild ? "pl-10" : ""
          }`}
        >
          {/* Expand/collapse toggle */}
          {hasChildren ? (
            <button
              onClick={() => toggleExpand(cat.id)}
              className="text-slate-400 hover:text-slate-600"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          ) : (
            <span className="w-4" />
          )}

          {/* Color dot */}
          <span
            className="h-3 w-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: cat.color }}
          />

          {/* Icon & name */}
          <span className="text-base">{cat.icon}</span>
          <span className="font-medium text-slate-800 text-sm">{cat.name}</span>

          {/* Badges */}
          {cat.isSystem ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
              <Shield className="h-3 w-3" />
              {t("systemBadge")}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-2 py-0.5 text-xs text-teal-700">
              <Sparkles className="h-3 w-3" />
              {t("customBadge")}
            </span>
          )}

          {/* Spacer */}
          <span className="flex-1" />

          {/* Stats */}
          <span className="text-xs text-slate-400">
            {t("transactionCount", { count: cat.transactionCount })}
          </span>
          <span
            className={`text-sm font-medium min-w-[90px] text-right ${
              cat.type === "income" ? "text-emerald-600" : "text-rose-600"
            }`}
          >
            {cat.type === "income" ? "+" : "-"}
            {formatCurrency(cat.totalAmount)}
          </span>

          {/* Actions — only for custom categories */}
          {!cat.isSystem && (
            <div className="flex gap-1 ml-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setEditingCategory(cat)}
                title={t("editCategory")}
              >
                <Pencil className="h-4 w-4 text-slate-400" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(cat.id)}
                title={t("deleteCategory")}
              >
                <Trash2 className="h-4 w-4 text-slate-400" />
              </Button>
            </div>
          )}
        </div>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="border-l-2 border-slate-100 ml-6">
            {children.map((child) => renderCategory(child, true))}
          </div>
        )}
      </div>
    );
  };

  /** Render a section (Expenses / Income). */
  const renderSection = (title: string, items: Category[], colorClass: string) => (
    <div className="space-y-1">
      <h3 className={`text-xs font-semibold uppercase tracking-wider px-4 pt-4 pb-2 ${colorClass}`}>
        {title}
      </h3>
      <div className="divide-y divide-slate-100">
        {items.map((cat) => renderCategory(cat))}
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Add category button */}
      <div className="flex justify-end">
        <Button onClick={() => setIsCreating(true)} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          {t("addCategory")}
        </Button>
      </div>

      {/* Create form */}
      {isCreating && (
        <CategoryForm
          categories={parents}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}

      {/* Edit form */}
      {editingCategory && (
        <CategoryForm
          category={editingCategory}
          categories={parents}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}

      {/* Category list */}
      <Card>
        <CardContent className="p-0">
          {renderSection(t("expenses"), expenseParents, "text-rose-500")}
          {renderSection(t("income"), incomeParents, "text-emerald-500")}
        </CardContent>
      </Card>
    </div>
  );
}
