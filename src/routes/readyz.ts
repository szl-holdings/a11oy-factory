import { createFileRoute } from "@tanstack/react-router";
import { readiness } from "@/lib/honest";

export const Route = createFileRoute("/readyz")({
  server: {
    handlers: {
      GET: async () => {
        const body = readiness();
        return Response.json(body, { status: body.production_ready ? 200 : 503 });
      },
      HEAD: async () => new Response(null, { status: 503 }),
    },
  },
});
