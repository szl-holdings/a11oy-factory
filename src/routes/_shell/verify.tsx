import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Page } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ReceiptCard } from "@/components/receipt-card";
import { StatusChip } from "@/components/truth-chip";
import {
  clearLedger,
  exportLedgerBundle,
  loadLedger,
  verifyReceipt,
  type VerifyResult,
} from "@/lib/ledger";
import { loadOwnerApproval, verifyAdmissionReceipt } from "@/lib/admission";
import type { AdmissionReceipt, DecisionReceipt } from "@/lib/types";

type Search = { hash?: string };

export const Route = createFileRoute("/_shell/verify")({
  validateSearch: (search: Record<string, unknown>): Search => ({
    hash: typeof search.hash === "string" ? search.hash : undefined,
  }),
  component: VerifyPage,
});

function VerifyPage() {
  const { hash } = Route.useSearch();
  const [paste, setPaste] = useState("");
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const ledger = useMemo(() => loadLedger(), [tick]);
  const admission = useMemo(() => loadOwnerApproval(), [tick]);

  useEffect(() => {
    if (!hash) return;
    const found = ledger.entries.find((e) => e.hash === hash);
    if (found) {
      setPaste(JSON.stringify(found, null, 2));
      return;
    }
    const admission = loadOwnerApproval();
    if (admission && admission.hash === hash) {
      setPaste(JSON.stringify(admission, null, 2));
    }
  }, [hash, ledger.entries]);

  async function onVerify() {
    setError(null);
    try {
      const parsed = JSON.parse(paste) as DecisionReceipt | AdmissionReceipt;
      if (parsed && "schema" in parsed && parsed.schema === "szl.owner-admission-receipt/v1") {
        const next = await verifyAdmissionReceipt(parsed as AdmissionReceipt);
        setResult({
          ok: next.ok,
          findings: next.findings,
          inLedger: next.inStore,
          chainOk: next.ok,
        });
        return;
      }
      const next = await verifyReceipt(parsed as DecisionReceipt);
      setResult(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "invalid JSON");
      setResult(null);
    }
  }

  function onExport() {
    const blob = new Blob([exportLedgerBundle()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "a11oy-ledger-bundle.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Page
      kicker="Offline-capable verifier"
      title="Verify a decision receipt"
      lede="Chain walks use the local durable ledger. Older receipts do not depend on a restarted in-process server. This preview still cannot walk the production a-11-oy.com chain."
    >
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Receipt JSON</CardTitle>
            <CardDescription>Paste a receipt or pick one from the ledger.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={paste}
              onChange={(e) => setPaste(e.target.value)}
              placeholder="{ schema, hash, ... }"
              aria-label="Receipt JSON"
            />
            {error && <p className="text-sm text-fail">{error}</p>}
            {result && (
              <div className="space-y-2 rounded-lg border border-border bg-elevated p-3 text-sm">
                <StatusChip value={result.ok ? "PASS" : "FAIL"} />
                <p>in ledger: {String(result.inLedger)} · chain: {String(result.chainOk)}</p>
                <ul className="text-muted">
                  {result.findings.length === 0 && <li>Hash and schema checks passed.</li>}
                  {result.findings.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button onClick={onVerify}>Verify</Button>
              <Button variant="secondary" onClick={onExport}>
                Export ledger bundle
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  clearLedger();
                  setTick((n) => n + 1);
                  setResult(null);
                }}
              >
                Clear local ledger
              </Button>
            </div>
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Local chain</CardTitle>
              <CardDescription>
                {ledger.entries.length} receipts · backend=localStorage (durable=true, browser-scoped)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {admission && (
                <button
                  type="button"
                  className="block w-full rounded-lg border border-pass/30 bg-pass/5 p-3 text-left text-sm hover:border-accent/40"
                  onClick={() => setPaste(JSON.stringify(admission, null, 2))}
                >
                  <span className="font-mono text-xs text-subtle">{admission.decision_id}</span>
                  <span className="mt-1 block">owner green light · APPROVED</span>
                </button>
              )}
              {ledger.entries
                .slice()
                .reverse()
                .slice(0, 6)
                .map((entry) => (
                  <button
                    key={entry.hash}
                    type="button"
                    className="block w-full rounded-lg border border-border bg-elevated p-3 text-left text-sm hover:border-accent/40"
                    onClick={() => setPaste(JSON.stringify(entry, null, 2))}
                  >
                    <span className="font-mono text-xs text-subtle">{entry.decision_id}</span>
                    <span className="mt-1 block">{entry.vertical_id} · {entry.decision.status}</span>
                  </button>
                ))}
            </CardContent>
          </Card>
          {ledger.entries[0] && <ReceiptCard receipt={ledger.entries[ledger.entries.length - 1]} compact />}
        </div>
      </div>
    </Page>
  );
}
