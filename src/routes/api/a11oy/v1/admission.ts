import { createFileRoute } from "@tanstack/react-router";
import { currentAdmission } from "@/lib/admission";

export const Route = createFileRoute("/api/a11oy/v1/admission")({
  server: {
    handlers: {
      GET: async () => Response.json(currentAdmission()),
    },
  },
});
