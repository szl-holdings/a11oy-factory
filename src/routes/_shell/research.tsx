import { createFileRoute, Link } from "@tanstack/react-router";
import { Page } from "@/components/app-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { profile } from "@/lib/data/registry";

export const Route = createFileRoute("/_shell/research")({
  component: ResearchPage,
});

function ResearchPage() {
  return (
    <Page
      kicker="Research portal"
      title="Proofs, formulas, and frontier"
      lede="Locked-8, semantic-verified, and conjecture stay distinct. No formula is a business oracle."
    >
      <Tabs defaultValue="formulas">
        <TabsList className="flex w-full flex-wrap justify-start">
          <TabsTrigger value="formulas">Formulas</TabsTrigger>
          <TabsTrigger value="frontier">Frontier</TabsTrigger>
          <TabsTrigger value="leaders">Leader patterns</TabsTrigger>
        </TabsList>
        <TabsContent value="formulas">
          <div className="grid gap-4">
            {profile.formula_bindings.map((item) => (
              <Card key={item.formula_id}>
                <CardHeader>
                  <div className="flex flex-wrap items-center gap-2">
                    <CardTitle>
                      {item.formula_id} · {item.name}
                    </CardTitle>
                    <Badge variant={item.proof_class.startsWith("LOCKED") ? "pass" : "warn"}>
                      {item.proof_class}
                    </Badge>
                    <Badge variant="fail">no authority</Badge>
                  </div>
                  <CardDescription>{item.allowed_runtime_binding}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-muted">
                  <p>{item.prohibited_claim}</p>
                  <p className="text-xs text-subtle">
                    Verticals: {item.verticals} · Evidence required: {item.required_binding_evidence}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="frontier">
          <p className="mb-4 text-sm text-muted">
            Owner order opened the program. Live acceptance runs on the Frontier workbench.
          </p>
          <Link
            to="/frontier"
            className="mb-6 inline-flex h-11 items-center text-sm text-accent underline-offset-4 hover:underline"
          >
            Open N1–N8 workbench
          </Link>
          <div className="grid gap-4 lg:grid-cols-2">
            {profile.frontier_program.map((item) => (
              <Card key={item.id}>
                <CardHeader>
                  <p className="font-mono text-xs text-subtle">
                    {item.id} · {item.priority}
                  </p>
                  <CardTitle>{item.name}</CardTitle>
                  <CardDescription>{item.novelty}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted">{item.build}</p>
                  <ul className="mt-3 space-y-1 text-xs text-subtle">
                    {item.acceptance.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        <TabsContent value="leaders">
          <p className="mb-4 text-sm text-muted">
            Clean-room public patterns only. No proprietary code, UX copying, or unsupported parity claims.
          </p>
          <div className="grid gap-4 lg:grid-cols-2">
            {profile.vertical_cells.map((cell) => (
              <Card key={cell.vertical_id}>
                <CardHeader>
                  <CardTitle>
                    <Link
                      to="/verticals/$id"
                      params={{ id: cell.vertical_id }}
                      className="hover:underline"
                    >
                      {cell.display_name.split("—")[0]}
                    </Link>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  {cell.leaders.map((leader) => (
                    <div key={leader.name}>
                      <a href={leader.url} className="text-accent underline-offset-4 hover:underline">
                        {leader.name}
                      </a>
                      <p className="text-muted">{leader.pattern}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </Page>
  );
}
