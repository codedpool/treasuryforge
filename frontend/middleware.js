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
 *
 * Basic Auth alone is not enough on its own, though: unlike a SameSite
 * cookie, the browser caches Basic Auth credentials per *origin* and
 * resends them automatically on every request to that origin, regardless
 * of which page triggered the request -- so a malicious page open in the
 * same browser could still cross-site POST to /api/wallet/reset and have
 * the browser attach valid, cached credentials on its own (verified: a
 * cross-origin POST with a mismatched Origin header and otherwise-correct
 * credentials succeeded before this check existed). State-mutating
 * requests additionally require the Origin header, when the browser sends
 * one, to match this app's own origin.
 */
export function middleware(request) {
  if (!SECRET) {
    return new NextResponse(
      "DASHBOARD_ACCESS_SECRET is not set. The dashboard refuses to serve wallet data or " +
        "destructive routes without it -- see frontend/.env.example.",
      { status: 500 }
    );
  }

  if (request.method !== "GET" && request.method !== "HEAD") {
    const origin = request.headers.get("origin");
    // Only reject a *mismatched* Origin, not a missing one -- CSRF relies
    // on a browser automatically attaching cached credentials to a
    // cross-site request; a non-browser client (curl, a script) has no
    // such ambient credentials to exploit, so there's nothing to protect
    // against there and blocking it would only break legitimate scripted use.
    if (origin && origin !== request.nextUrl.origin) {
      return new NextResponse("Cross-origin request rejected", { status: 403 });
    }
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
