import { NextResponse } from "next/server";

const TRUEFORGE_URL = (process.env.TRUEFORGE_URL || "http://127.0.0.1:8790").replace(/\/$/, "");

/**
 * TrueForge, not the wallet server, owns approval-checkpoint state -- a
 * paused turn lives in TrueForge's own session/trace model. Rather than
 * guessing at an unverified checkpoint-list/approve API shape and shipping
 * something that might call the wrong endpoint, this proxies TrueForge's
 * documented session list so the dashboard can show real connectivity and
 * link straight into TrueForge's own built-in UI (which already has an
 * approve/reject affordance) for acting on a pending checkpoint. See
 * components/dashboard/ApprovalQueue.jsx.
 */
// See lib/walletProxy.js's identical comment -- a stalled (not just
// refused) upstream would otherwise hang this request indefinitely.
const TRUEFORGE_FETCH_TIMEOUT_MS = 10_000;

export async function GET() {
  try {
    const res = await fetch(`${TRUEFORGE_URL}/api/v1/sessions`, {
      cache: "no-store",
      signal: AbortSignal.timeout(TRUEFORGE_FETCH_TIMEOUT_MS),
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return NextResponse.json({ error: "trueforge_error", status: res.status }, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "trueforge_unreachable", message: String(err?.message || err) },
      { status: 502 }
    );
  }
}
