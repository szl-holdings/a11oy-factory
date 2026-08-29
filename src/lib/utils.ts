import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCount(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

export function formatKb(kb: number): string {
  if (kb >= 1_000_000) return `${(kb / 1_000_000).toFixed(1)} GB`;
  if (kb >= 1_000) return `${(kb / 1_000).toFixed(1)} MB`;
  return `${kb} KB`;
}

export function shortId(value: string, keep = 8): string {
  if (value.length <= keep * 2 + 1) return value;
  return `${value.slice(0, keep)}…${value.slice(-6)}`;
}

export function evidenceLabel(cls: string): string {
  return cls.replaceAll("_", " ");
}
