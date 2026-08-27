import { NextResponse } from "next/server";
import { walletFetch } from "@/lib/walletProxy";
import { proxyJson } from "@/lib/proxyResponse";

// Allowlisted, not forwarded blind -- these map 1:1 onto the wallet
// server's own POST /debug/trigger-approval* routes (see mcp-server/app/server.py).
const TRIGGER_PATHS = {
  "daily-drawdown": "/debug/trigger-approval",
  concentration: "/debug/trigger-approval/concentration",
  "sell-all": "/debug/trigger-approval/sell-all",
  "consecutive-losses": "/debug/trigger-approval/consecutive-losses",
};

export async function POST(request, { params }) {
  const path = TRIGGER_PATHS[params.trigger];
  if (!path) {
    return NextResponse.json({ error: "unknown_trigger", trigger: params.trigger }, { status: 404 });
  }
  const search = new URL(request.url).search;
  return proxyJson(walletFetch(`${path}${search}`, { method: "POST" }));
}
