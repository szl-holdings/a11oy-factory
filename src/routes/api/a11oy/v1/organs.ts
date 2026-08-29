import { createFileRoute } from "@tanstack/react-router";
import { organCatalog } from "@/lib/organs";

export const Route = createFileRoute("/api/a11oy/v1/organs")({
  server: {
    handlers: {
      GET: async () => Response.json(organCatalog()),
    },
  },
});
