"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Zap, ArrowRight, Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // No backend auth endpoint — navigate after brief feedback delay.
    setTimeout(() => router.push("/workspace"), 800);
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center relative overflow-hidden px-4">
      {/* ─── Ambient glow ────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0" aria-hidden="true">
        <div className="absolute top-[30%] left-[40%] w-[500px] h-[500px] rounded-full bg-accent-glow opacity-30 blur-[120px]" />
      </div>

      <motion.div
        className="relative z-10 w-full max-w-sm"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Logo */}
        <div className="flex items-center justify-center gap-2.5 mb-10">
          <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/25 flex items-center justify-center">
            <Zap size={20} className="text-accent" />
          </div>
          <span className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            Opti-Twin
          </span>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-border bg-bg-200 p-8">
          <h1 className="text-lg font-semibold text-text-primary font-[family-name:var(--font-display)] mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-text-tertiary mb-6">Sign in to your workspace</p>

          <form className="space-y-4" onSubmit={handleSignIn}>
            <div>
              <label className="type-label block mb-1.5">Email</label>
              <Input type="email" placeholder="you@company.com" disabled={loading} />
            </div>
            <div>
              <label className="type-label block mb-1.5">Password</label>
              <Input type="password" placeholder="••••••••" disabled={loading} />
            </div>
            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? <><Loader2 size={14} className="animate-spin" /> Signing in…</> : <>Sign In <ArrowRight size={14} /></>}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-bg-200 px-3 text-[11px] text-text-muted uppercase tracking-wider">or continue with</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Button variant="secondary" size="md" onClick={handleSignIn} disabled={loading}>Google</Button>
            <Button variant="secondary" size="md" onClick={handleSignIn} disabled={loading}>SSO</Button>
          </div>
        </div>

        <p className="text-center text-xs text-text-muted mt-6">
          Don&apos;t have an account?{" "}
          <a href="#" className="text-accent hover:text-accent-light transition-colors">Get started free</a>
        </p>
      </motion.div>
    </div>
  );
}
