"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Plus, Pencil, Trash2, ScrollText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  MOCK_RULES,
  MOCK_CATEGORIES,
  type CategorizationRule,
} from "@/lib/mock-categories";
import { RuleForm } from "./rule-form";

/** Label mapping for match types */
const MATCH_TYPE_KEYS: Record<string, string> = {
  contains: "matchContains",
  exact: "matchExact",
  regex: "matchRegex",
  starts_with: "matchStartsWith",
};

/** Badge colors for match types */
const MATCH_TYPE_COLORS: Record<string, string> = {
  contains: "bg-blue-50 text-blue-700",
  exact: "bg-purple-50 text-purple-700",
  regex: "bg-amber-50 text-amber-700",
  starts_with: "bg-cyan-50 text-cyan-700",
};

/**
 * Categorization rules list with add / edit / delete support.
 */
export function RulesList() {
  const t = useTranslations("categories");
  const [rules, setRules] = useState<CategorizationRule[]>(MOCK_RULES);
  const [editingRule, setEditingRule] = useState<CategorizationRule | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const handleDelete = (id: string) => {
    if (!window.confirm(t("confirmDeleteRule"))) return;
    setRules((prev) => prev.filter((r) => r.id !== id));
  };

  const handleSave = (rule: CategorizationRule) => {
    setRules((prev) => {
      const exists = prev.find((r) => r.id === rule.id);
      if (exists) return prev.map((r) => (r.id === rule.id ? rule : r));
      return [...prev, rule];
    });
    setEditingRule(null);
    setIsCreating(false);
  };

  const handleCancel = () => {
    setEditingRule(null);
    setIsCreating(false);
  };

  return (
    <div className="space-y-4">
      {/* Add rule button */}
      <div className="flex justify-end">
        <Button onClick={() => setIsCreating(true)} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          {t("addRule")}
        </Button>
      </div>

      {/* Create form */}
      {isCreating && (
        <RuleForm
          categories={MOCK_CATEGORIES}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}

      {/* Edit form */}
      {editingRule && (
        <RuleForm
          rule={editingRule}
          categories={MOCK_CATEGORIES}
          onSave={handleSave}
          onCancel={handleCancel}
        />
      )}

      {/* Rules table */}
      {rules.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ScrollText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-500">{t("noRules")}</p>
            <p className="text-xs text-slate-400 mt-1">{t("noRulesHint")}</p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="text-left px-4 py-3 font-medium text-slate-600">
                      {t("rulePattern")}
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-slate-600">
                      {t("ruleMatchType")}
                    </th>
                    <th className="text-left px-4 py-3 font-medium text-slate-600">
                      {t("ruleCategory")}
                    </th>
                    <th className="text-center px-4 py-3 font-medium text-slate-600">
                      {t("rulePriority")}
                    </th>
                    <th className="text-right px-4 py-3 font-medium text-slate-600 w-24" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rules
                    .sort((a, b) => b.priority - a.priority)
                    .map((rule) => (
                      <tr key={rule.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-xs text-slate-800">
                          {rule.pattern}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                              MATCH_TYPE_COLORS[rule.matchType]
                            }`}
                          >
                            {t(MATCH_TYPE_KEYS[rule.matchType])}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-700">
                          {rule.categoryName}
                        </td>
                        <td className="px-4 py-3 text-center text-slate-500">
                          {rule.priority}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setEditingRule(rule)}
                              title={t("editRule")}
                            >
                              <Pencil className="h-4 w-4 text-slate-400" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDelete(rule.id)}
                              title={t("deleteRule")}
                            >
                              <Trash2 className="h-4 w-4 text-slate-400" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
