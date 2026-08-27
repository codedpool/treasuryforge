"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/decisions", label: "Decision log" },
  { href: "/dashboard/approvals", label: "Approval queue" },
  { href: "/dashboard/risk", label: "Risk panel" },
  { href: "/dashboard/quant-desk", label: "Quant Desk" },
  { href: "/dashboard/audit", label: "Audit export" },
];

export default function DashboardNav() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-1 overflow-x-auto md:flex-col md:gap-0.5">
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={[
              "whitespace-nowrap rounded px-3 py-2 font-mono text-xs uppercase tracking-wideish transition",
              active
                ? "bg-ink-overlay text-signal-amber"
                : "text-ink-muted hover:bg-ink-overlay/60 hover:text-ink-bright",
            ].join(" ")}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
