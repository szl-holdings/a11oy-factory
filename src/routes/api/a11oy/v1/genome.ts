import { createFileRoute } from "@tanstack/react-router";
import { genome } from "@/lib/honest";

export const Route = createFileRoute("/api/a11oy/v1/genome")({
  server: {
    handlers: {
      GET: async () => Response.json(genome()),
    },
  },
});
