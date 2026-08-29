import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EffectChip, EvidenceChip } from "@/components/truth-chip";
import { verticalById } from "@/lib/data/registry";
import { evaluatePolicy } from "@/lib/policy";
import { scenarioById } from "@/lib/scenarios";

const TRACKS = [
  { id: "T-7", x: 38, y: 42, scenario: "killinchu-geofence-ok", label: "Track 7 — provenance" },
  { id: "T-9", x: 62, y: 58, scenario: "killinchu-effector-request", label: "Track 9 — prohibited request" },
  { id: "T-2", x: 22, y: 70, scenario: "killinchu-no-provenance", label: "Track 2 — no provenance" },
];

export function KillinchuSim() {
  const vertical = verticalById("killinchu")!;
  const [selected, setSelected] = useState(TRACKS[0].id);
  const track = TRACKS.find((t) => t.id === selected) ?? TRACKS[0];
  const scenario = scenarioById(track.scenario)!;
  const result = useMemo(
    () => evaluatePolicy(vertical, scenario, "LOG_ONLY"),
    [vertical, scenario],
  );

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Bounded simulation</CardTitle>
          <CardDescription>
            SIMULATED data. Proposal-only. Human-approved. No weapon command, target engagement,
            autonomous interdiction, or physical effector.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative overflow-hidden rounded-lg border border-border bg-elevated">
            <svg
              viewBox="0 0 100 80"
              className="h-auto w-full"
              role="img"
              aria-label="Synthetic geofence map with three tracks"
            >
              <rect width="100" height="80" fill="#121214" />
              <polygon
                points="18,18 82,16 86,62 22,70"
                fill="rgba(197,205,200,0.06)"
                stroke="#c5cdc8"
                strokeWidth="0.4"
              />
              <text x="20" y="15" fill="#6e6e68" fontSize="3">
                declared geofence (synthetic)
              </text>
              {TRACKS.map((item) => (
                <g key={item.id}>
                  <circle
                    cx={item.x}
                    cy={item.y}
                    r={selected === item.id ? 3.2 : 2.2}
                    fill={selected === item.id ? "#c5cdc8" : "#7d8fa3"}
                  />
                  <text x={item.x + 4} y={item.y + 1} fill="#f2f1ec" fontSize="3">
                    {item.id}
                  </text>
                </g>
              ))}
            </svg>
            <p className="sr-only">Equivalent table follows the figure.</p>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Synthetic tracks and policy outcomes</caption>
              <thead className="text-xs uppercase tracking-wide text-subtle">
                <tr>
                  <th className="py-2 pr-3">Track</th>
                  <th className="py-2 pr-3">Scenario</th>
                  <th className="py-2">Select</th>
                </tr>
              </thead>
              <tbody>
                {TRACKS.map((item) => (
                  <tr key={item.id} className="border-t border-border">
                    <td className="py-2 pr-3 font-mono">{item.id}</td>
                    <td className="py-2 pr-3 text-muted">{item.label}</td>
                    <td className="py-2">
                      <Button
                        size="sm"
                        variant={selected === item.id ? "default" : "outline"}
                        onClick={() => setSelected(item.id)}
                      >
                        Inspect
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{track.label}</CardTitle>
          <CardDescription>{scenario.summary}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <EvidenceChip value={scenario.evidence[0]?.class ?? "UNAVAILABLE"} />
            <EffectChip value={result.effect} />
          </div>
          <ul className="space-y-1 text-sm text-muted">
            {result.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <p className="text-xs text-subtle">
            Public software stops at recommendation, denial, or escalation. Physical authority remains
            outside this system. Durability of the public Space is EPHEMERAL; this preview ledger is
            browser-local only.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
