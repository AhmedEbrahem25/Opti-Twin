"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded-lg border border-border bg-bg-300 px-3 py-1.5 text-sm text-text-primary",
        "placeholder:text-text-muted",
        "focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent/40",
        "transition-all duration-[var(--dur-fast)] ease-[var(--ease-out)]",
        "disabled:cursor-not-allowed disabled:opacity-40",
        "file:border-0 file:bg-transparent file:text-sm file:font-medium",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
