import Image from "next/image";
import Link from "next/link";
import DashboardNav from "@/components/dashboard/DashboardNav";
import StatusBadge from "@/components/dashboard/StatusBadge";
import ResetButton from "@/components/dashboard/ResetButton";

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-paper">
      {/* The same lake-at-dusk frame as the landing hero, blended down to
          near-invisible behind the parchment -- ties the dashboard back to
          the same product rather than reading as a separate, generic app. */}
      <header className="grain-paper relative overflow-hidden border-b border-paper-line bg-paper-raised">
        <Image
          src="/harness3.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-center mix-blend-multiply"
        />
        <div className="absolute inset-0 bg-paper-raised/90" />

        <div className="relative z-10 mx-auto max-w-7xl px-6 py-4 md:px-8">
          <div className="flex items-center justify-between gap-4">
            <Link href="/" className="shrink-0">
              <Image
                src="/logo.png"
                alt="TreasuryForge"
                width={1239}
                height={1270}
                priority
                className="h-9 w-auto md:h-11"
              />
            </Link>
            <div className="flex items-center gap-5">
              <StatusBadge />
              <ResetButton />
            </div>
          </div>
          <div className="mt-4 border-t border-paper-line/60 pt-1">
            <DashboardNav />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 pb-16 pt-8 md:px-8 md:pb-20 md:pt-10">{children}</main>
    </div>
  );
}
