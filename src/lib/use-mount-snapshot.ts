import { useMemo } from "react";
import { useHydrated } from "@tanstack/react-router";

/** Read a browser-backed value after hydration; subsequent edits stay in local state. */
export function useMountSnapshot<T>(read: () => T): T | null {
  const hydrated = useHydrated();
  return useMemo(() => hydrated ? read() : null, [hydrated, read]);
}
