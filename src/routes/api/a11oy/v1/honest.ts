import { createFileRoute } from "@tanstack/react-router";
import { buildHonest } from "@/lib/honest";

export const Route = createFileRoute("/api/a11oy/v1/honest")({
  server: {
    handlers: {
      GET: async () => Response.json(buildHonest()),
    },
  },
});
