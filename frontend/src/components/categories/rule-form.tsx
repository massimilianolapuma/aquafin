"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Category, CategorizationRule, MatchType } from "@/lib/mock-categories";

interface RuleFormProps {
  /** Existing rule to edit, or undefined for create. */
  rule?: CategorizationRule;
  /** All categories (for the dropdown). */
  categories: Category[];
  /** Called with the new/updated rule on save. */
  onSave: (rule: CategorizationRule) => void;
  /** Called when the user cancels. */
  onCancel: () => void;
}

const MATCH_TYPES: MatchType[] = ["contains", "exact", "regex", "starts_with"];

/** Match type translation keys */
const MATCH_KEYS: Record<MatchType, string> = {
  contains: "matchContains",
  exact: "matchExact",
  regex: "matchRegex",
  starts_with: "matchStartsWith",
};

/**
 * Inline form for creating or editing a categorization rule.
 */
export function RuleForm({ rule, categories, onSave, onCancel }: RuleFormProps) {
  const t = useTranslations("categories");

  const [pattern, setPattern] = useState(rule?.pattern ?? "");
  const [matchType, setMatchType] = useState<MatchType>(rule?.matchType ?? "contains");
  const [categoryId, setCategoryId] = useState(rule?.categoryId ?? "");
  const [priority, setPriority] = useState(rule?.priority ?? 10);

  // Flatten categories for dropdown (only leaf or any)
  const categoryOptions = categories.filter((c) => c.parentId !== null || !categories.some((ch) => ch.parentId === c.id));
  // If a category has no children it's a valid target; also include parents that have no children
  const allLeaves = categories.filter(
    (c) => !categories.some((ch) => ch.parentId === c.id),
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pattern.trim() || !categoryId) return;

    const selectedCat = categories.find((c) => c.id === categoryId);

    const saved: CategorizationRule = {
      id: rule?.id ?? `rule-${Date.now()}`,
      pattern: pattern.trim(),
      matchType,
      categoryId,
      categoryName: selectedCat?.name ?? "",
      priority,
    };
    onSave(saved);
  };

  return (
    <Card className="border-teal-200 bg-teal-50/30">
      <CardHeader className="pb-4">
        <CardTitle className="text-base">
          {rule ? t("editRule") : t("addRule")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Pattern */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("rulePattern")}
            </label>
            <Input
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
              placeholder="es. ESSELUNGA"
              required
            />
          </div>

          {/* Match type */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("ruleMatchType")}
            </label>
            <select
              value={matchType}
              onChange={(e) => setMatchType(e.target.value as MatchType)}
              className="flex h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
            >
              {MATCH_TYPES.map((mt) => (
                <option key={mt} value={mt}>
                  {t(MATCH_KEYS[mt])}
                </option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("ruleCategory")}
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
              className="flex h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-950"
            >
              <option value="">—</option>
              {allLeaves.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.icon} {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              {t("rulePriority")}
            </label>
            <Input
              type="number"
              min={1}
              max={100}
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-24"
            />
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
