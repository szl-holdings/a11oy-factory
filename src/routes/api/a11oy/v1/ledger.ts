import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/api/a11oy/v1/ledger")({
  server: {
    handlers: {
      GET: async () =>
        Response.json({
          schema: "szl.a11oy-ledger/v1",
          public_serving: "read-only",
          durable: true,
          backend: "browser localStorage in this preview",
          append: "not accepted on this public endpoint",
          note: "Decision receipts are appended only by the governed UI in the same browser. Export a self-contained bundle from /verify.",
        }),
      POST: async () =>
        Response.json(
          {
            error: "public ledger is read-only",
          },
          { status: 405 },
        ),
    },
  },
});
