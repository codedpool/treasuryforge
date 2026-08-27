import Link from "next/link";
import DashboardNav from "@/components/dashboard/DashboardNav";
import StatusBadge from "@/components/dashboard/StatusBadge";
import ResetButton from "@/components/dashboard/ResetButton";

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-ink">
      <header className="grain-ink relative border-b border-ink-line bg-ink-raised px-6 py-4 md:px-8">
        <div className="relative z-10 flex items-center justify-between">
          <Link href="/" className="font-display text-lg text-ink-bright">
            TreasuryForge
          </Link>
          <div className="flex items-center gap-5">
            <StatusBadge />
            <ResetButton />
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6 md:flex-row md:gap-10 md:px-8 md:py-10">
        <aside className="md:w-48 md:shrink-0">
          <DashboardNav />
        </aside>
        <main className="min-w-0 flex-1 pb-16">{children}</main>
      </div>
    </div>
  );
}
