import { Badge } from "@/components/ui/badge";
import type { EvidenceClass, PolicyEffect, DecisionStatus } from "@/lib/types";

const evidenceVariant: Record<EvidenceClass, "pass" | "warn" | "fail" | "info" | "default" | "accent"> = {
  MEASURED: "pass",
  PROVED: "pass",
  REPORTED: "info",
  SIMULATED: "warn",
  MODELED: "warn",
  CONJECTURE: "warn",
  UNAVAILABLE: "fail",
};

export function EvidenceChip({ value }: { value: EvidenceClass }) {
  return (
    <Badge variant={evidenceVariant[value]} title={`Evidence class: ${value}`}>
      {value}
    </Badge>
  );
}

export function PriorityChip({ value }: { value: string }) {
  const variant = value === "P0" ? "fail" : value === "P1" ? "warn" : "default";
  return <Badge variant={variant}>{value}</Badge>;
}

export function StatusChip({ value }: { value: string }) {
  const v = value.toUpperCase();
  const variant =
    v.includes("PASS") ||
    v === "READY" ||
    v === "APPROVED" ||
    v === "VERIFIED" ||
    v.includes("ADMITTED") ||
    v.includes("CLASSIFIED") ||
    v.includes("LIFTED") ||
    v === "OPEN" ||
    v === "SATISFIED" ||
    v.includes("GREEN")
      ? "pass"
      : v.includes("FAIL") || v === "DENIED" || v === "BLOCKED" || v === "ERROR"
        ? "fail"
        : v.includes("WARN") || v.includes("PLANNED") || v === "ESCALATED" || v === "PARTIAL"
          ? "warn"
          : "default";
  return <Badge variant={variant}>{value}</Badge>;
}

export function EffectChip({ value }: { value: PolicyEffect | DecisionStatus }) {
  const v = String(value);
  const variant = v.includes("DENY") || v === "DENIED"
    ? "fail"
    : v.includes("ESCALATE") || v === "ESCALATED" || v.includes("ABSTAIN")
      ? "warn"
      : v.includes("ALLOW") || v === "APPROVED" || v === "AWAITING_APPROVAL"
        ? "pass"
        : "default";
  return <Badge variant={variant}>{v.replaceAll("_", " ")}</Badge>;
}

export function TruthStrip({
  evidence,
  runtime,
  authority,
  freshness,
  limitations,
}: {
  evidence: string;
  runtime: string;
  authority: string;
  freshness: string;
  limitations: string;
}) {
  return (
    <dl className="grid grid-cols-2 gap-3 rounded-lg border border-border bg-elevated p-3 text-xs sm:grid-cols-5">
      <div>
        <dt className="uppercase tracking-wide text-subtle">Evidence</dt>
        <dd className="mt-1 text-fg">{evidence}</dd>
      </div>
      <div>
        <dt className="uppercase tracking-wide text-subtle">Runtime</dt>
        <dd className="mt-1 text-fg">{runtime}</dd>
      </div>
      <div>
        <dt className="uppercase tracking-wide text-subtle">Authority</dt>
        <dd className="mt-1 text-fg">{authority}</dd>
      </div>
      <div>
        <dt className="uppercase tracking-wide text-subtle">Freshness</dt>
        <dd className="mt-1 text-fg">{freshness}</dd>
      </div>
      <div className="col-span-2 sm:col-span-1">
        <dt className="uppercase tracking-wide text-subtle">Limits</dt>
        <dd className="mt-1 text-muted">{limitations}</dd>
      </div>
    </dl>
  );
}
