"use client";

import { useLocale } from "next-intl";
import { useRouter, usePathname } from "@/i18n/routing";

/** Toggle between Italian and English locales. */
export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const nextLocale = locale === "it" ? "en" : "it";
  const label = locale === "it" ? "🇬🇧 EN" : "🇮🇹 IT";

  function handleSwitch() {
    router.replace(pathname, { locale: nextLocale });
  }

  return (
    <button
      onClick={handleSwitch}
      className="rounded-md px-2 py-1 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
      aria-label={`Switch to ${nextLocale === "it" ? "Italian" : "English"}`}
    >
      {label}
    </button>
  );
}
