import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { FrontierWorkbench } from "@/components/frontier-workbench";
import { OwnerOrderBanner } from "@/components/owner-order-banner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { OWNER_ORDER } from "@/lib/admission";

export const Route = createFileRoute("/_shell/frontier")({
  component: FrontierPage,
});

function FrontierPage() {
  return (
    <Page
      kicker="Frontier program"
      title="Green light approved. N1–N8 is live."
      lede="Owner order AO-2026-08-29-001 is approved. Eight programs, one runtime. No new public forks."
    >
      <OwnerOrderBanner />
      <div className="mt-10">
        <FrontierWorkbench />
      </div>
      <Card className="mt-10">
        <CardHeader>
          <CardTitle>Order remaining closed</CardTitle>
          <CardDescription>
            Green light is not a production certificate and not a Hub mutation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted">
            {OWNER_ORDER.still_prohibits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <ul className="mt-4 space-y-1 text-xs text-subtle">
            {OWNER_ORDER.truth_boundary.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </Page>
  );
}
