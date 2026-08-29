import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/_shell/console/observability")({
  component: () => <Navigate to="/console" />,
});
