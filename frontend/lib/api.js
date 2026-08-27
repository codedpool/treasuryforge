"use client";

import useSWR from "swr";

async function fetcher(url) {
  const res = await fetch(url);
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.message || "Request failed");
    err.kind = data?.error || "unknown_error";
    err.status = res.status;
    throw err;
  }
  return data;
}

const swrConfig = {
  refreshInterval: 15_000,
  revalidateOnFocus: true,
  shouldRetryOnError: false,
};

export function usePortfolio() {
  return useSWR("/api/wallet/portfolio", fetcher, swrConfig);
}

export function useTransactions(limit = 50) {
  return useSWR(`/api/wallet/transactions?limit=${limit}`, fetcher, swrConfig);
}

export function useMetrics() {
  return useSWR("/api/wallet/metrics", fetcher, swrConfig);
}

export function useRiskSummary() {
  return useSWR("/api/wallet/risk-summary", fetcher, swrConfig);
}

export function useEquityCurve() {
  return useSWR("/api/wallet/equity-curve", fetcher, swrConfig);
}

export function useTrueforgeSessions() {
  return useSWR("/api/trueforge/sessions", fetcher, { ...swrConfig, refreshInterval: 8_000 });
}

export function isTrueforgeUnreachable(error) {
  return error?.kind === "trueforge_unreachable";
}

/** The browser-visible TrueForge URL for "open in TrueForge" links -- a
 * plain localhost address, not a secret, so NEXT_PUBLIC_ is fine here
 * (unlike WALLET_SHARED_SECRET, which never leaves lib/walletProxy.js). */
export const TRUEFORGE_PUBLIC_URL = process.env.NEXT_PUBLIC_TRUEFORGE_URL || "http://127.0.0.1:8790";

export async function resetWallet() {
  return postJson("/api/wallet/reset");
}

export async function forceTrigger(trigger, params = {}) {
  const qs = new URLSearchParams(params).toString();
  return postJson(`/api/wallet/trigger/${trigger}${qs ? `?${qs}` : ""}`);
}

async function postJson(url) {
  const res = await fetch(url, { method: "POST" });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.message || "Request failed");
    err.kind = data?.error || "unknown_error";
    err.status = res.status;
    throw err;
  }
  return data;
}

/** True when the last SWR error was a proxied "wallet server unreachable"
 * response -- the dashboard's most common real-world empty state, since it
 * means the wallet server (mcp-server) just isn't running yet. */
export function isWalletUnreachable(error) {
  return error?.kind === "wallet_unreachable";
}
