import "server-only";
import { NextResponse } from "next/server";

/** Runs a walletFetch call and normalizes both HTTP-level and
 * network-level failures into one shape the dashboard's fetch wrapper can
 * branch on -- an unreachable wallet server (not started, wrong port) is a
 * real, expected state, not an exception to swallow. */
export async function proxyJson(fetchPromise) {
  try {
    const res = await fetchPromise;
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      return NextResponse.json(
        { error: "wallet_error", status: res.status, message: data?.error || data?.detail || "Wallet server returned an error." },
        { status: res.status }
      );
    }
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: "wallet_unreachable", message: String(err?.message || err) },
      { status: 502 }
    );
  }
}
