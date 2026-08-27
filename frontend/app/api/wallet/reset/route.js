import { walletFetch } from "@/lib/walletProxy";
import { proxyJson } from "@/lib/proxyResponse";

export async function POST() {
  return proxyJson(walletFetch("/debug/reset", { method: "POST" }));
}
