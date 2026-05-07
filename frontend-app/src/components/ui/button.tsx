"use client";
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-[var(--dur-fast)] ease-[var(--ease-out)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:pointer-events-none disabled:opacity-40 cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-accent text-bg hover:bg-accent-light shadow-sm active:scale-[0.98]",
        secondary: "bg-bg-400 text-text-primary border border-border hover:border-border-hover hover:bg-bg-500 active:scale-[0.98]",
        ghost: "text-text-secondary hover:text-text-primary hover:bg-bg-400",
        destructive: "bg-danger/15 text-danger border border-danger/20 hover:bg-danger/25 hover:border-danger/40",
        outline: "border border-border-hover text-text-primary hover:bg-accent-muted hover:border-accent/40 hover:shadow-glow active:scale-[0.98]",
        accent: "bg-accent-muted text-accent border border-accent/20 hover:border-accent/40 hover:bg-accent/20",
        link: "text-accent underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        sm: "h-8 px-3 text-xs rounded-md",
        md: "h-9 px-4 text-sm",
        lg: "h-11 px-6 text-sm",
        xl: "h-12 px-8 text-base",
        icon: "h-9 w-9 p-0",
        "icon-sm": "h-7 w-7 p-0",
      },
    },
    defaultVariants: { variant: "default", size: "md" },
  }
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
