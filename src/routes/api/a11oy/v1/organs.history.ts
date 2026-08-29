import { createFileRoute } from "@tanstack/react-router";
import { recentOrganRuns } from "@/lib/organs";

export const Route = createFileRoute("/api/a11oy/v1/organs/history")({
  server: {
    handlers: {
      GET: async () =>
        Response.json({
          schema: "szl.organ-history/v1",
          durable: "process-local",
          entries: recentOrganRuns(40),
        }),
    },
  },
});
