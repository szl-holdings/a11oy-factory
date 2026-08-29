import { createFileRoute, Link } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { profile } from "@/lib/data/registry";

export const Route = createFileRoute("/_shell/company")({
  component: CompanyPage,
});

function CompanyPage() {
  const h = profile.product_hierarchy;
  return (
    <Page
      kicker="SZL Holdings"
      title="Buyer first, then proof, then limits"
      lede="Lyte Services is the wedge. A11oy is the control plane. Alloy Runtime is not a second flagship. Broad unverified 'proven / running / air-gap' claims are out of scope."
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Product hierarchy</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted">
            <p>
              <span className="text-fg">{h.core_product.name}.</span> {h.core_product.one_sentence}
            </p>
            <p>
              <span className="text-fg">{h.primary_vertical.name}.</span> {h.primary_vertical.role}
            </p>
            <p>
              <span className="text-fg">{h.adjacent_vertical.name}.</span> {h.adjacent_vertical.role}
            </p>
            <p>
              <span className="text-fg">{h.public_reference.name}.</span> {h.public_reference.role}
            </p>
            <p>{h.internal_engine.rule}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Business stage</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted">
            <p>Mission: {profile.mission}</p>
            <p>Binding decision: {profile.primary_recommendation}</p>
            <p>Admission freeze is required until the registry is authoritative and Lyte is admitted as a protected pilot.</p>
            <p>Retired or incubated names are not current products: {h.retired_or_incubated.join(", ")}.</p>
          </CardContent>
        </Card>
      </div>
      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Link
          to="/investor"
          className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
        >
          Investor proof
        </Link>
        <Link
          to="/verticals/$id"
          params={{ id: "lyte-services" }}
          className="inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
        >
          Lyte cell
        </Link>
      </div>
    </Page>
  );
}
