"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  LayoutDashboard,
  ArrowLeftRight,
  Wallet,
  Tags,
  Upload,
  BarChart3,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  /** Translation key inside the "nav" namespace */
  labelKey: string;
  /** Route path appended after /[locale] */
  href: string;
  /** Lucide icon component */
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { labelKey: "dashboard", href: "/dashboard", icon: LayoutDashboard },
  { labelKey: "transactions", href: "/transactions", icon: ArrowLeftRight },
  { labelKey: "accounts", href: "/accounts", icon: Wallet },
  { labelKey: "categories", href: "/categories", icon: Tags },
  { labelKey: "import", href: "/import", icon: Upload },
  { labelKey: "analytics", href: "/analytics", icon: BarChart3 },
  { labelKey: "settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  /** Whether the sidebar is open (mobile only) */
  open?: boolean;
  /** Callback to close the sidebar (mobile only) */
  onClose?: () => void;
}

/** Responsive sidebar navigation with collapsible mobile drawer. */
export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const t = useTranslations("nav");

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Logo area */}
        <div className="flex h-14 items-center border-b border-slate-200 px-4">
          <Link
            href="/dashboard"
            className="text-xl font-bold text-primary-600"
            onClick={onClose}
          >
            Aquafin
          </Link>
        </div>

        {/* Navigation links */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.includes(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary-50 text-primary-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {t(item.labelKey)}
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
