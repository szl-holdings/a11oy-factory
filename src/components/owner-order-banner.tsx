import { useEffect, useState } from "react";
import { Link } from "@tanstack/react-router";
import { OWNER_ORDER, ensureOwnerApproval, loadOwnerApproval } from "@/lib/admission";
import { StatusChip } from "@/components/truth-chip";
import type { AdmissionReceipt } from "@/lib/types";
import { shortId } from "@/lib/utils";

export function OwnerOrderBanner({ compact = false }: { compact?: boolean }) {
  const [receipt, setReceipt] = useState<AdmissionReceipt | null>(null);

  useEffect(() => {
    const existing = loadOwnerApproval();
    if (existing) {
      setReceipt(existing);
      return;
    }
    void ensureOwnerApproval().then(setReceipt);
  }, []);

  return (
    <aside className="rounded-xl border border-pass/30 bg-pass/5 p-4 sm:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <StatusChip value="APPROVED" />
        <StatusChip value="LIFTED" />
        <StatusChip value="CLASSIFIED" />
        <StatusChip value="ADMITTED" />
        <p className="font-mono text-[11px] text-subtle">{OWNER_ORDER.order_id}</p>
      </div>
      {compact ? (
        <p className="mt-3 text-sm text-muted">
          Green light approved. Freeze lifted. Nexus classified. Lyte admitted. Frontier N1–N8 is
          open.{" "}
          <Link to="/admission" className="text-accent underline-offset-4 hover:underline">
            View the receipt
          </Link>
        </p>
      ) : (
        <>
          <p className="mt-3 max-w-3xl text-pretty text-sm text-muted">{OWNER_ORDER.instruction}</p>
          <p className="mt-2 text-xs text-subtle">
            Still closed: {OWNER_ORDER.still_prohibits.join(" · ")}
          </p>
          {receipt && (
            <p className="mt-2 font-mono text-[11px] text-subtle">
              receipt {shortId(receipt.hash, 10)} · {receipt.actor}
            </p>
          )}
          <Link
            to="/admission"
            className="mt-3 inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
          >
            Open admission desk
          </Link>
        </>
      )}
    </aside>
  );
}
