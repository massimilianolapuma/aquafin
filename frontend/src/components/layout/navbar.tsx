"use client";

import { Menu } from "lucide-react";
import { UserButton } from "@clerk/nextjs";
import { LocaleSwitcher } from "@/components/layout/locale-switcher";

interface NavbarProps {
  /** Callback to toggle the mobile sidebar */
  onMenuToggle?: () => void;
}

/** Top navigation bar with mobile menu toggle, locale switcher, and user button. */
export function Navbar({ onMenuToggle }: NavbarProps) {
  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
      {/* Left: mobile hamburger + app name (shown on small screens) */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100 lg:hidden"
          aria-label="Toggle menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="text-lg font-bold text-primary-600 lg:hidden">
          Aquafin
        </span>
      </div>

      {/* Right: locale switcher + Clerk user button */}
      <div className="flex items-center gap-3">
        <LocaleSwitcher />
        <UserButton afterSignOutUrl="/" />
      </div>
    </header>
  );
}
