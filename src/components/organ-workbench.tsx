import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusChip, EvidenceChip } from "@/components/truth-chip";
import { ORGANS, runOrgan, type OrganDef, type OrganReceipt } from "@/lib/organs";

export function OrganWorkbench() {
  const [active, setActive] = useState(ORGANS[0]!.id);
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState<OrganReceipt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const organ = useMemo(() => ORGANS.find((o) => o.id === active)!, [active]);

  async function run(def: OrganDef, text: string) {
    setBusy(true);
    setError(null);
    try {
      const result = await runOrgan(def.id, { prompt: text });
      setReceipt(result);
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
          <CardDescription>{organ.job}. Factory-live. Not a public Space. Formulas never grant authority.</CardDescription>
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
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
