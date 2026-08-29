import type { HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium tracking-wide uppercase tabular-nums",
  {
    variants: {
      variant: {
        default: "border-border text-muted bg-elevated",
        pass: "border-pass/30 text-pass bg-pass/10",
        warn: "border-warn/30 text-warn bg-warn/10",
        fail: "border-fail/30 text-fail bg-fail/10",
        info: "border-info/30 text-info bg-info/10",
        accent: "border-accent/30 text-accent bg-accent/10",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export function Badge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
