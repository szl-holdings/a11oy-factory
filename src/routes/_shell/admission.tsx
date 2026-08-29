import { useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusChip } from "@/components/truth-chip";
import {
  OWNER_ORDER,
  approveOwnerOrder,
  ensureOwnerApproval,
  verifyAdmissionReceipt,
} from "@/lib/admission";
import type { AdmissionReceipt } from "@/lib/types";
import { shortId } from "@/lib/utils";

export const Route = createFileRoute("/_shell/admission")({
  component: AdmissionPage,
});

function AdmissionPage() {
  const [receipt, setReceipt] = useState<AdmissionReceipt | null>(null);
  const [verified, setVerified] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void ensureOwnerApproval().then(setReceipt);
  }, []);

  async function onApprove() {
    setBusy(true);
    try {
      const next = await approveOwnerOrder("estate owner");
      setReceipt(next);
      setVerified("APPROVED — already on the local admission ledger");
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    if (!receipt) return;
    const result = await verifyAdmissionReceipt(receipt);
    setVerified(result.ok ? "VERIFIED" : result.findings.join("; "));
  }

  return (
    <Page
      kicker="Owner admission desk"
      title="Green light approved."
      lede="The estate owner approved order AO-2026-08-29-001. That lifts the freeze for factory internals. It does not certify production or mutate Hub or GitHub."
    >
      <div className="grid min-w-0 gap-4 lg:grid-cols-2">
        <Card className="min-w-0">
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              <StatusChip value="APPROVED" />
              <StatusChip value="GREEN_LIGHT" />
            </div>
            <CardTitle>{OWNER_ORDER.order_id}</CardTitle>
            <CardDescription>
              Issued {OWNER_ORDER.issued_at} · Approved {OWNER_ORDER.approved_at}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-pretty text-sm text-muted">{OWNER_ORDER.instruction}</p>
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs uppercase tracking-wide text-subtle">Freeze</dt>
                <dd className="mt-1">{OWNER_ORDER.effects.freeze}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-subtle">Nexus</dt>
                <dd className="mt-1">{OWNER_ORDER.effects.nexus.classification}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-subtle">Lyte</dt>
                <dd className="mt-1">{OWNER_ORDER.effects.lyte.admission}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-subtle">Frontier</dt>
                <dd className="mt-1">{OWNER_ORDER.effects.frontier}</dd>
              </div>
            </dl>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button onClick={() => void onApprove()} disabled={busy || Boolean(receipt)}>
                {receipt ? "Already approved" : "Approve green light"}
              </Button>
              <Button variant="secondary" onClick={() => void onVerify()} disabled={!receipt}>
                Verify receipt
              </Button>
            </div>
            {verified && <p className="text-sm text-pass">{verified}</p>}
          </CardContent>
        </Card>
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>Admission receipt</CardTitle>
            <CardDescription>
              Hash-chained, local, unsigned preview. Formulas still grant no authority.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {receipt ? (
              <div className="space-y-3">
                <p className="font-mono text-[11px] text-subtle">
                  {receipt.decision_id} · {shortId(receipt.hash, 12)}
                </p>
                <p className="text-sm text-muted">
                  Actor {receipt.actor}. Effect {receipt.effect}. Production ready{" "}
                  {String(receipt.production_ready)}.
                </p>
                <pre className="max-h-[360px] max-w-full overflow-x-auto overflow-y-auto break-all rounded-lg border border-border bg-elevated p-4 font-mono text-[11px] leading-relaxed text-muted">
                  {JSON.stringify(receipt, null, 2)}
                </pre>
                <a
                  href={`/verify?hash=${encodeURIComponent(receipt.hash)}`}
                  className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
                >
                  Open in verifier
                </a>
              </div>
            ) : (
              <p className="text-sm text-muted">Writing the owner receipt…</p>
            )}
          </CardContent>
        </Card>
      </div>
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Still closed</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted">
            {OWNER_ORDER.still_prohibits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="mt-6 flex flex-col gap-2 sm:flex-row">
            <Button asChild>
              <Link to="/frontier">Open frontier</Link>
            </Button>
            <Button variant="secondary" asChild>
              <Link to="/verticals/$id" params={{ id: "lyte-services" }}>
                Lyte cell
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </Page>
  );
}
