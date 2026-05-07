"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Zap, Brain, Factory, BarChart3, Shield, Globe,
  ArrowRight, ChevronRight, Activity, Box, Search,
} from "lucide-react";

const features = [
  { icon: Factory, title: "Multi-Factory Management", desc: "Monitor and control unlimited factories, production lines, and machines from a single platform." },
  { icon: Brain, title: "AI Optimization Engine", desc: "Reinforcement learning agent optimizes energy costs, machine health, and production schedules in real-time." },
  { icon: Box, title: "Digital Twin Visualization", desc: "Interactive 3D digital twins with live sensor overlays and thermal visualization for every machine." },
  { icon: Activity, title: "Real-Time Telemetry", desc: "Sub-second streaming telemetry from industrial sensors with intelligent anomaly detection." },
  { icon: Search, title: "Explainable AI Decisions", desc: "Every AI recommendation comes with human-readable reasoning — full transparency, zero black boxes." },
  { icon: Shield, title: "Enterprise Security", desc: "SOC2 compliant, role-based access control, audit logs, and end-to-end encryption." },
];

const stats = [
  { value: "18%", label: "Avg. Energy Reduction" },
  { value: "99.2%", label: "Uptime Guarantee" },
  { value: "< 3s", label: "Decision Latency" },
  { value: "47+", label: "Machine Types" },
];

const easeOut: [number, number, number, number] = [0.16, 1, 0.3, 1];

const fadeUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: easeOut },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg relative overflow-hidden">
      {/* ─── Ambient Background Glow ─────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0" aria-hidden="true">
        <div className="absolute top-[10%] left-[20%] w-[600px] h-[600px] rounded-full bg-accent-glow opacity-40 blur-[100px]" />
        <div className="absolute bottom-[20%] right-[15%] w-[400px] h-[400px] rounded-full bg-cyan/5 opacity-30 blur-[100px]" />
      </div>

      {/* ─── Navbar ──────────────────────────────── */}
      <header className="relative z-10 flex items-center justify-between px-6 md:px-12 h-16 border-b border-border/50">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/25 flex items-center justify-center">
            <Zap size={16} className="text-accent" />
          </div>
          <span className="text-base font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            Opti-Twin
          </span>
        </div>
        <nav className="hidden md:flex items-center gap-8 text-sm text-text-secondary">
          <a href="#features" className="hover:text-text-primary transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-text-primary transition-colors">How It Works</a>
          <a href="#pricing" className="hover:text-text-primary transition-colors">Pricing</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Log In</Button>
          </Link>
          <Link href="/workspace">
            <Button variant="outline" size="sm">
              Dashboard <ArrowRight size={14} />
            </Button>
          </Link>
        </div>
      </header>

      {/* ─── Hero ────────────────────────────────── */}
      <section className="relative z-10 flex flex-col items-center text-center pt-24 pb-20 px-6">
        <motion.div {...fadeUp}>
          <span className="type-label inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-bg-200 mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-accent pulse-live" />
            AI-Powered Industrial Optimization Platform
          </span>
        </motion.div>

        <motion.h1
          className="text-4xl md:text-6xl lg:text-7xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight leading-[0.95] max-w-4xl mb-6"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: easeOut, delay: 0.1 }}
        >
          Optimize Every Machine.{" "}
          <span className="gradient-text">Save Every Watt.</span>
        </motion.h1>

        <motion.p
          className="text-base md:text-lg text-text-secondary max-w-xl mb-10 leading-relaxed"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2, ease: easeOut }}
        >
          Connect your industrial equipment. Stream real-time telemetry. Let AI optimize energy costs,
          prevent failures, and maximize production — with full explainability.
        </motion.p>

        <motion.div
          className="flex items-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35, ease: easeOut }}
        >
          <Link href="/workspace">
            <Button size="xl">
              Enter Dashboard <ArrowRight size={16} />
            </Button>
          </Link>
          <Link href="#features">
            <Button variant="secondary" size="xl">
              Learn More
            </Button>
          </Link>
        </motion.div>

        {/* ─── Stats Row ─────────────────────────── */}
        <motion.div
          className="flex flex-wrap justify-center gap-8 md:gap-16 mt-20 pt-10 border-t border-border/50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.5 }}
        >
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-2xl md:text-3xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
                {s.value}
              </p>
              <p className="text-xs text-text-tertiary mt-1">{s.label}</p>
            </div>
          ))}
        </motion.div>
      </section>

      {/* ─── Features Grid ───────────────────────── */}
      <section id="features" className="relative z-10 px-6 md:px-12 py-20 max-w-6xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <span className="type-label mb-3 block">Capabilities</span>
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            Enterprise-Grade Industrial Intelligence
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              className="group p-6 rounded-xl border border-border bg-bg-200 hover:border-border-hover hover:bg-bg-300 transition-all duration-300 spotlight-card"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                e.currentTarget.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
                e.currentTarget.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
              }}
            >
              <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center mb-4 group-hover:bg-accent/15 transition-colors">
                <f.icon size={20} className="text-accent" />
              </div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">{f.title}</h3>
              <p className="text-xs text-text-tertiary leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── How It Works ────────────────────────── */}
      <section id="how-it-works" className="relative z-10 px-6 md:px-12 py-20 max-w-4xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <span className="type-label mb-3 block">Process</span>
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
            Three Steps to Intelligent Operations
          </h2>
        </motion.div>

        <div className="space-y-6">
          {[
            { step: "01", title: "Connect Your Equipment", desc: "Add factories, production lines, and machines. Configure sensors and telemetry endpoints. Our wizard handles the setup." },
            { step: "02", title: "Stream & Monitor", desc: "Real-time telemetry flows into live dashboards. Digital twins visualize machine state. Anomalies are detected instantly." },
            { step: "03", title: "AI Optimizes Everything", desc: "Our RL agent analyzes data patterns, predicts failures, shifts loads, and recommends actions — with full XAI explanations for every decision." },
          ].map((item, i) => (
            <motion.div
              key={item.step}
              className="flex gap-6 p-6 rounded-xl border border-border bg-bg-200"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
            >
              <span className="text-3xl font-bold text-accent/30 font-[family-name:var(--font-display)] shrink-0">
                {item.step}
              </span>
              <div>
                <h3 className="text-base font-semibold text-text-primary mb-1">{item.title}</h3>
                <p className="text-sm text-text-tertiary leading-relaxed">{item.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── CTA ─────────────────────────────────── */}
      <section className="relative z-10 px-6 py-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight mb-4">
            Ready to Optimize?
          </h2>
          <p className="text-text-secondary mb-8 max-w-md mx-auto">
            Start monitoring your industrial operations with AI-powered intelligence today.
          </p>
          <Link href="/workspace">
            <Button size="xl">
              Get Started Free <ArrowRight size={16} />
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* ─── Footer ──────────────────────────────── */}
      <footer className="relative z-10 border-t border-border px-6 md:px-12 py-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-accent" />
            <span className="text-xs text-text-tertiary">© 2026 Opti-Twin. Built with ⚡ by Team Opti-Twin</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-text-tertiary">
            <a href="#" className="hover:text-text-secondary transition-colors">Privacy</a>
            <a href="#" className="hover:text-text-secondary transition-colors">Terms</a>
            <a href="#" className="hover:text-text-secondary transition-colors">Documentation</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
