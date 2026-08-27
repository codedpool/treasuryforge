import { walletFetch } from "@/lib/walletProxy";
import { proxyJson } from "@/lib/proxyResponse";

export async function GET(request) {
  const limit = new URL(request.url).searchParams.get("limit") || "50";
  return proxyJson(walletFetch(`/ui/transactions?limit=${encodeURIComponent(limit)}`));
}
