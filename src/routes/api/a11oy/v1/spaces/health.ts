import { createFileRoute } from "@tanstack/react-router";
import { spacesHealth } from "@/lib/honest";

export const Route = createFileRoute("/api/a11oy/v1/spaces/health")({
  server: {
    handlers: {
      GET: async () => Response.json(spacesHealth()),
    },
  },
});
