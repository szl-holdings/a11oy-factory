import { createFileRoute } from "@tanstack/react-router";
import { liveness } from "@/lib/honest";

export const Route = createFileRoute("/healthz")({
  server: {
    handlers: {
      GET: async () => Response.json(liveness()),
      HEAD: async () => new Response(null, { status: 200 }),
    },
  },
});
