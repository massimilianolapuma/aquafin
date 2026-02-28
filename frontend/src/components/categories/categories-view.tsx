"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Tags, ScrollText } from "lucide-react";
import { CategoryList } from "./category-list";
import { RulesList } from "./rules-list";

type Tab = "categories" | "rules";

/**
 * Main categories management view with two tabs:
 * - Categories: hierarchical category list with CRUD
 * - Rules: categorization rules list with CRUD
 */
export function CategoriesView() {
  const t = useTranslations("categories");
  const [activeTab, setActiveTab] = useState<Tab>("categories");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t("title")}</h1>
        <p className="text-sm text-slate-500 mt-1">{t("subtitle")}</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-200">
        <button
          onClick={() => setActiveTab("categories")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "categories"
              ? "border-teal-600 text-teal-600"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Tags className="h-4 w-4" />
          {t("tabCategories")}
        </button>
        <button
          onClick={() => setActiveTab("rules")}
          className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "rules"
              ? "border-teal-600 text-teal-600"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <ScrollText className="h-4 w-4" />
          {t("tabRules")}
        </button>
      </div>

      {/* Tab content */}
      {activeTab === "categories" ? <CategoryList /> : <RulesList />}
    </div>
  );
}
