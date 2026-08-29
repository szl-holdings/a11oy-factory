import { createFileRoute } from "@tanstack/react-router";
import { tabMatrix } from "@/lib/honest";

export const Route = createFileRoute("/api/a11oy/tab-matrix")({
  server: {
    handlers: {
      GET: async () =>
        Response.json({
          schema: "szl.a11oy-tab-matrix/v1",
          routes: tabMatrix(),
        }),
    },
  },
});
