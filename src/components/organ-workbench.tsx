import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusChip, EvidenceChip } from "@/components/truth-chip";
import { ORGANS, type OrganDef, type OrganReceipt } from "@/lib/organs";
import { loadOrganLedger, runOrganViaApi } from "@/lib/organ-ledger";

export function OrganWorkbench() {
  const [active, setActive] = useState(ORGANS[0]!.id);
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState<OrganReceipt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState(() => loadOrganLedger().entries.slice(-6).reverse());
  const organ = useMemo(() => ORGANS.find((o) => o.id === active)!, [active]);

  async function run(def: OrganDef, text: string) {
    setBusy(true);
    setError(null);
    try {
      const result = await runOrganViaApi(def.id, text);
      setReceipt(result);
      setHistory(loadOrganLedger().entries.slice(-6).reverse());
    } catch (err) {
      setError(err instanceof Error ? err.message : "run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        {ORGANS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => {
              setActive(item.id);
              setReceipt(null);
              setPrompt("");
            }}
            className={`min-w-0 rounded-xl border p-3 text-left transition-colors duration-150 ${
              active === item.id ? "border-accent/50 bg-elevated" : "border-border bg-surface hover:border-accent/30"
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <p className="font-mono text-[11px] text-subtle">{item.id}</p>
              <Badge variant="pass">LIVE</Badge>
            </div>
            <p className="mt-1 font-serif text-base tracking-tight">{item.title}</p>
            <p className="mt-1 truncate text-xs text-subtle">{item.job}</p>
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-mono text-xs text-subtle">{organ.id}</p>
            <StatusChip value="READY" />
            <EvidenceChip value={organ.evidence_class} />
            <Badge>{organ.body}</Badge>
          </div>
          <CardTitle>{organ.title}</CardTitle>
          <CardDescription>
            {organ.job}. POST /api/a11oy/v1/organs/{organ.id}. Not a public Space. Formulas never grant authority.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form
            className="flex flex-col gap-3 sm:flex-row"
            onSubmit={(event) => {
              event.preventDefault();
              void run(organ, prompt);
            }}
          >
            <Input
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder={organ.placeholder}
              aria-label={`${organ.title} input`}
            />
            <Button type="submit" disabled={busy} className="sm:w-40">
              {busy ? "Running…" : "Run organ"}
            </Button>
          </form>
          {error && <p className="text-sm text-fail">{error}</p>}
          {receipt && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <StatusChip value={receipt.status} />
                <EvidenceChip value={receipt.evidence_class} />
                <span className="break-all font-mono text-[11px] text-subtle">{receipt.hash.slice(0, 24)}…</span>
              </div>
              <pre className="max-h-[420px] overflow-auto rounded-lg border border-border bg-elevated p-4 text-xs text-muted">
                {JSON.stringify(receipt, null, 2)}
              </pre>
              <ul className="space-y-1 text-xs text-subtle">
                {receipt.limitations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <a
                href={`/verify?hash=${receipt.hash}`}
                className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
              >
                Verify this receipt
              </a>
            </div>
          )}
          {history.length > 0 && (
            <div className="border-t border-border pt-4">
              <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-subtle">Browser organ ledger</p>
              <ul className="space-y-2">
                {history.map((item) => (
                  <li key={item.hash} className="flex flex-wrap items-center gap-2 text-xs text-muted">
                    <StatusChip value={item.status} />
                    <span className="font-mono">{item.id}</span>
                    <span>{item.title}</span>
                    <span className="break-all font-mono text-subtle">{item.hash.slice(0, 16)}…</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
