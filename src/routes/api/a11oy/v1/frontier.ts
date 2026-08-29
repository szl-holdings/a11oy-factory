import { createFileRoute } from "@tanstack/react-router";
import { OWNER_ORDER } from "@/lib/admission";
import { profile } from "@/lib/data/registry";

export const Route = createFileRoute("/api/a11oy/v1/frontier")({
  server: {
    handlers: {
      GET: async () =>
        Response.json({
          schema: "szl.frontier-program/v1",
          owner_order_id: OWNER_ORDER.order_id,
          freeze: OWNER_ORDER.effects.freeze,
          status: OWNER_ORDER.effects.frontier,
          items: profile.frontier_program.map((item) => ({
            id: item.id,
            name: item.name,
            priority: item.priority,
            novelty: item.novelty,
          })),
          note: "Live acceptance is evaluated in the factory UI. This endpoint is the static program contract.",
        }),
    },
  },
});
