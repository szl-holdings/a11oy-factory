import { createFileRoute } from "@tanstack/react-router";
import { spacePlan } from "@/lib/spaces";

export const Route = createFileRoute("/api/a11oy/v1/spaces")({
  server: {
    handlers: {
      GET: async () => Response.json(spacePlan()),
    },
  },
});
