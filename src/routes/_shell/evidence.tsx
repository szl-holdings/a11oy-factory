import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/_shell/evidence")({
  component: () => <Navigate to="/trust" />,
});
