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
    <nav className="flex gap-1 overflow-x-auto">
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={[
              "whitespace-nowrap border-b-2 px-3 py-2.5 font-mono text-xs uppercase tracking-wideish transition",
              active
                ? "border-signal-amber-ink text-signal-amber-ink"
                : "border-transparent text-paper-muted hover:border-paper-line hover:text-paper-ink",
            ].join(" ")}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
