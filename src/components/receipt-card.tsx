import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EffectChip, EvidenceChip } from "@/components/truth-chip";
import type { DecisionReceipt } from "@/lib/types";
import { shortId } from "@/lib/utils";

export function ReceiptCard({
  receipt,
  compact = false,
}: {
  receipt: DecisionReceipt;
  compact?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-lg">{receipt.vertical_id}</CardTitle>
          <EffectChip value={receipt.decision.status} />
        </div>
        <p className="font-mono text-[11px] text-subtle">
          {receipt.decision_id} · {shortId(receipt.hash, 10)}
        </p>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-pretty text-muted">{receipt.proposal.summary}</p>
        <p>
          <span className="text-subtle">Action </span>
          {receipt.proposal.action}
          <span className="text-subtle"> — cannot grant authority</span>
        </p>
        <ul className="space-y-1 text-muted">
          {receipt.policy.reasons.slice(0, compact ? 2 : 6).map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
        {!compact && (
          <div className="flex flex-wrap gap-1.5">
            {receipt.evidence.map((item) => (
              <EvidenceChip key={item.evidence_id} value={item.class} />
            ))}
          </div>
        )}
        <div className="flex flex-wrap gap-3 text-xs text-subtle">
          <span>policy {receipt.policy.revision}</span>
          <span>outcome {receipt.outcome_state}</span>
          <span>{receipt.authority.approved ? `approved by ${receipt.authority.actor}` : "human pending"}</span>
        </div>
        <a
          href={`/verify?hash=${encodeURIComponent(receipt.hash)}`}
          className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
        >
          Verify this receipt
        </a>
      </CardContent>
    </Card>
  );
}
