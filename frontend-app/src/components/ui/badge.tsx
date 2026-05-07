"use client";
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full text-[11px] font-medium tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default: "bg-bg-400 text-text-secondary border border-border",
        success: "bg-success-muted text-success border border-success/20",
        warning: "bg-warning-muted text-warning border border-warning/20",
        danger: "bg-danger-muted text-danger border border-danger/20",
        info: "bg-info-muted text-info border border-info/20",
        accent: "bg-accent-muted text-accent border border-accent/20",
        outline: "border border-border-hover text-text-secondary",
      },
      size: {
        sm: "px-2 py-0.5 text-[10px]",
        md: "px-2.5 py-0.5",
        lg: "px-3 py-1 text-xs",
      },
    },
    defaultVariants: { variant: "default", size: "md" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  pulse?: boolean;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, pulse, children, ...props }, ref) => (
    <span ref={ref} className={cn(badgeVariants({ variant, size, className }))} {...props}>
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75 pulse-live",
            variant === "success" && "bg-success",
            variant === "warning" && "bg-warning",
            variant === "danger" && "bg-danger",
            variant === "info" && "bg-info",
            variant === "accent" && "bg-accent",
            (!variant || variant === "default" || variant === "outline") && "bg-text-tertiary",
          )} />
          <span className={cn(
            "relative inline-flex rounded-full h-2 w-2",
            variant === "success" && "bg-success",
            variant === "warning" && "bg-warning",
            variant === "danger" && "bg-danger",
            variant === "info" && "bg-info",
            variant === "accent" && "bg-accent",
            (!variant || variant === "default" || variant === "outline") && "bg-text-tertiary",
          )} />
        </span>
      )}
      {children}
    </span>
  )
);
Badge.displayName = "Badge";

export { Badge, badgeVariants };
