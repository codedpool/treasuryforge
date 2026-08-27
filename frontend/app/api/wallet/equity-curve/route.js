import { walletFetch } from "@/lib/walletProxy";
import { proxyJson } from "@/lib/proxyResponse";

export async function GET() {
  return proxyJson(walletFetch("/ui/equity-curve"));
}
