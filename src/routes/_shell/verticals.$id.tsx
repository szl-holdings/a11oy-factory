import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Page } from "@/components/app-shell";
import { DecisionTheatre } from "@/components/decision-theatre";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { compileVertical, type CompiledCell } from "@/lib/compiler";
import { cellOverlay } from "@/lib/admission";
import { formulaIds, verticalById } from "@/lib/data/registry";
import { StatusChip } from "@/components/truth-chip";

export const Route = createFileRoute("/_shell/verticals/$id")({
  component: VerticalPage,
});

function VerticalPage() {
  const { id } = Route.useParams();
  const cell = verticalById(id);
  const [compiled, setCompiled] = useState<CompiledCell | null>(null);

  useEffect(() => {
    if (!cell) return;
    void compileVertical(cell, formulaIds()).then(setCompiled);
  }, [cell]);

  if (!cell) throw notFound();
  const overlay = cellOverlay(cell.vertical_id);

  return (
    <Page kicker={cell.portfolio_role.replaceAll("_", " ")} title={cell.display_name} lede={cell.buyer}>
      <div className="mb-6 flex flex-wrap gap-2">
        <StatusChip value={overlay.admitted ? "ADMITTED" : overlay.space_visibility} />
        <Badge>{overlay.label}</Badge>
        <Badge variant={overlay.admitted ? "pass" : "fail"}>{overlay.public_launch}</Badge>
      </div>
      <p className="max-w-3xl text-pretty text-muted">{cell.decision_problem}</p>
      <p className="mt-3 max-w-3xl text-sm text-subtle">{cell.original_szl_design}</p>

      <Tabs defaultValue="theatre" className="mt-10">
        <TabsList className="flex w-full flex-wrap justify-start">
          <TabsTrigger value="theatre">Decision theatre</TabsTrigger>
          <TabsTrigger value="policy">Policy</TabsTrigger>
          <TabsTrigger value="compiled">Compiled contracts</TabsTrigger>
        </TabsList>
        <TabsContent value="theatre">
          <DecisionTheatre vertical={cell} />
        </TabsContent>
        <TabsContent value="policy">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Allowed</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted">
                {cell.allowed_actions.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Prohibited</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted">
                {cell.prohibited_actions.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Human authority</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted">
                {cell.human_authority.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Negative tests</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted">
                {cell.negative_tests.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="compiled">
          {!compiled && <p className="text-sm text-muted">Compiling manifest…</p>}
          {compiled && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Build identity</CardTitle>
                  <CardDescription>
                    {compiled.valid ? "Manifest validates." : compiled.errors.join("; ")}
                  </CardDescription>
                </CardHeader>
                <CardContent className="font-mono text-xs text-muted">
                  <p>digest {compiled.manifest_digest}</p>
                  <p>space {cell.hf_space_id}</p>
                  <p>formulas {cell.formula_bindings.join(", ")}</p>
                </CardContent>
              </Card>
              <pre className="max-h-[480px] overflow-auto rounded-xl border border-border bg-elevated p-4 font-mono text-[11px] leading-relaxed text-muted">
                {JSON.stringify(compiled.contracts, null, 2)}
              </pre>
            </div>
          )}
        </TabsContent>
      </Tabs>
      <p className="mt-8 text-sm">
        <Link to="/research" className="text-accent underline-offset-4 hover:underline">
          Formula bindings
        </Link>
      </p>
    </Page>
  );
}
