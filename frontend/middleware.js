import { NextResponse } from "next/server";

const SECRET = process.env.DASHBOARD_ACCESS_SECRET;

/**
 * Every app/api/wallet/* and app/api/trueforge/* route runs server-side and
 * attaches WALLET_SHARED_SECRET on the wallet's behalf -- but that only
 * protects the *second* hop (Next.js -> wallet server). Without a gate of
 * its own, the Next.js app itself is a fully unauthenticated proxy: anyone
 * who can reach it gets full read access to portfolio/transaction/risk
 * data and can call the destructive reset/force-trigger routes, with no
 * need to ever know WALLET_SHARED_SECRET (a real Qodo finding on PR #8).
 *
 * HTTP Basic Auth via middleware, checked against a *separate*
 * DASHBOARD_ACCESS_SECRET, was chosen over a custom login flow because it
 * needs zero UI code -- the browser's own native credential prompt and
 * cache handle everything -- and matches this project's existing "a
 * localhost bind is not the security boundary, a shared secret is" posture
 * (see mcp-server's own README) rather than inventing a second, different
 * security model. Fails closed: an unset secret blocks every gated route
 * rather than silently leaving them open.
 */
export function middleware(request) {
  if (!SECRET) {
    return new NextResponse(
      "DASHBOARD_ACCESS_SECRET is not set. The dashboard refuses to serve wallet data or " +
        "destructive routes without it -- see frontend/.env.example.",
      { status: 500 }
    );
  }

  const authHeader = request.headers.get("authorization") || "";
  const [scheme, encoded] = authHeader.split(" ");
  if (scheme === "Basic" && encoded) {
    try {
      const decoded = atob(encoded);
      const password = decoded.slice(decoded.indexOf(":") + 1);
      if (password === SECRET) {
        return NextResponse.next();
      }
    } catch {
      // fall through to 401
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="TreasuryForge dashboard"' },
  });
}

export const config = {
  matcher: ["/dashboard/:path*", "/api/wallet/:path*", "/api/trueforge/:path*"],
};
