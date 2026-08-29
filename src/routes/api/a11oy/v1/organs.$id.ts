import { createFileRoute } from "@tanstack/react-router";
import { organById, runOrgan } from "@/lib/organs";

export const Route = createFileRoute("/api/a11oy/v1/organs/$id")({
  server: {
    handlers: {
      GET: async ({ params }) => {
        const organ = organById(params.id);
        if (!organ) return Response.json({ error: "unknown organ" }, { status: 404 });
        return Response.json(organ);
      },
      POST: async ({ params, request }) => {
        const organ = organById(params.id);
        if (!organ) return Response.json({ error: "unknown organ" }, { status: 404 });
        let body: { prompt?: string; payload?: Record<string, string | number | boolean> } = {};
        try {
          body = (await request.json()) as typeof body;
        } catch {
          body = {};
        }
        const receipt = await runOrgan(params.id, body);
        return Response.json(receipt, { status: receipt.status === "DENIED" ? 200 : 200 });
      },
    },
  },
});
