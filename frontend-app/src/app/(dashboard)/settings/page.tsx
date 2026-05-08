"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { User, Building2, Key, Bell, Brain, Settings2 } from "lucide-react";
import { useTelemetryStore } from "@/store/telemetry-store";
import { useWorkspaceStore } from "@/store/workspace-store";
import { api, type ProfileName } from "@/lib/api";
import Link from "next/link";

const PROFILE_WEIGHTS: Record<ProfileName, { alpha: number; beta: number; gamma: number }> = {
  default:              { alpha: 1.0, beta: 0.9, gamma: 1.8 },
  cost_first:          { alpha: 2.0, beta: 0.5, gamma: 0.8 },
  equipment_sensitive: { alpha: 0.8, beta: 2.0, gamma: 1.0 },
  production_critical: { alpha: 0.8, beta: 0.7, gamma: 2.5 },
  quality_focused:     { alpha: 1.2, beta: 1.5, gamma: 1.5 },
};

export default function SettingsPage() {
  const orgName = useWorkspaceStore((s) => s.currentOrg?.name ?? "Ezz Steel");
  const aiProfile = useTelemetryStore((s) => s.aiProfile);
  const setAIProfile = useTelemetryStore((s) => s.setAIProfile);
  const dpeMode = useTelemetryStore((s) => s.dpeMode);
  const isConnected = useTelemetryStore((s) => s.isConnected);

  const router = useRouter();
  const w = PROFILE_WEIGHTS[aiProfile];
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.setProfile(aiProfile);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // optimistic — store already updated
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">
          Settings
        </h1>
        <p className="text-sm text-text-tertiary mt-0.5">
          Workspace, AI configuration, and integrations
        </p>
      </div>

      <div className="space-y-4">
        {/* Organization */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-bg-400 border border-border flex items-center justify-center">
                <Building2 size={16} className="text-text-tertiary" />
              </div>
              <div>
                <CardTitle>Organization</CardTitle>
                <p className="text-[11px] text-text-tertiary mt-0.5">Organization profile and backend connection</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: "Organization Name", value: orgName, type: "text" },
                { label: "Plan", value: "Enterprise", type: "badge" },
                { label: "Region", value: "Middle East — Egypt", type: "text" },
                { label: "Backend URL", value: process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000", type: "mono" },
                {
                  label: "Backend Status",
                  value: isConnected ? "Connected (WS live)" : "Offline",
                  type: "status",
                },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-xs text-text-secondary">{item.label}</span>
                  {item.type === "badge" ? (
                    <Badge variant="accent" size="sm">{item.value}</Badge>
                  ) : item.type === "mono" ? (
                    <code className="text-xs font-mono text-text-tertiary bg-bg-400 px-2 py-0.5 rounded">{item.value}</code>
                  ) : item.type === "status" ? (
                    <Badge variant={isConnected ? "success" : "outline"} size="sm">{item.value}</Badge>
                  ) : (
                    <span className="text-xs text-text-primary">{item.value}</span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Account */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-bg-400 border border-border flex items-center justify-center">
                <User size={16} className="text-text-tertiary" />
              </div>
              <div>
                <CardTitle>Account</CardTitle>
                <p className="text-[11px] text-text-tertiary mt-0.5">Your personal account settings</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: "Name", value: "Ahmed Ibrahim", type: "text" },
                { label: "Email", value: "ahmed@ezz-steel.com", type: "text" },
                { label: "Role", value: "Admin", type: "badge" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-xs text-text-secondary">{item.label}</span>
                  {item.type === "badge" ? (
                    <Badge variant="accent" size="sm">{item.value}</Badge>
                  ) : (
                    <span className="text-xs text-text-primary">{item.value}</span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Configuration */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-bg-400 border border-border flex items-center justify-center">
                <Brain size={16} className="text-accent" />
              </div>
              <div className="flex-1 flex items-center justify-between">
                <div>
                  <CardTitle>AI Configuration</CardTitle>
                  <p className="text-[11px] text-text-tertiary mt-0.5">Reward profile and engine settings</p>
                </div>
                <Link href="/ai-control">
                  <Button variant="ghost" size="sm" className="text-xs"><Settings2 size={13} /> Full Control</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-secondary">Active Profile</span>
                <div className="flex items-center gap-2">
                  <Badge variant="accent" size="sm">{aiProfile}</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-secondary">Energy Weight (α)</span>
                <Input type="number" value={w.alpha} readOnly className="w-20 h-7 text-xs text-right opacity-70" />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-secondary">Machine Stress Weight (β)</span>
                <Input type="number" value={w.beta} readOnly className="w-20 h-7 text-xs text-right opacity-70" />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-secondary">Production Delay Weight (γ)</span>
                <Input type="number" value={w.gamma} readOnly className="w-20 h-7 text-xs text-right opacity-70" />
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-xs text-text-secondary">Pricing Mode</span>
                <Badge variant="outline" size="sm">{dpeMode}</Badge>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-xs text-text-secondary">Decision Interval</span>
                <span className="text-xs text-text-primary">3 seconds</span>
              </div>
              <div className="pt-2 flex flex-wrap gap-2">
                {(Object.keys(PROFILE_WEIGHTS) as ProfileName[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => { setAIProfile(p); api.setProfile(p).catch(() => {}); }}
                    className={`text-[11px] px-2.5 py-1 rounded-md border transition-all ${aiProfile === p ? "bg-accent/10 border-accent/50 text-accent" : "bg-bg-300 border-border text-text-tertiary hover:border-border-hover"}`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-bg-400 border border-border flex items-center justify-center">
                <Bell size={16} className="text-text-tertiary" />
              </div>
              <div>
                <CardTitle>Notifications</CardTitle>
                <p className="text-[11px] text-text-tertiary mt-0.5">Alert thresholds and notification channels</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: "Email Notifications", value: "Enabled", type: "badge" },
                { label: "Critical Alert SMS", value: "Enabled", type: "badge" },
                { label: "AI Decision Digest", value: "Hourly", type: "text" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-xs text-text-secondary">{item.label}</span>
                  {item.type === "badge" ? (
                    <Badge variant="success" size="sm">{item.value}</Badge>
                  ) : (
                    <span className="text-xs text-text-primary">{item.value}</span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-bg-400 border border-border flex items-center justify-center">
                <Key size={16} className="text-text-tertiary" />
              </div>
              <div>
                <CardTitle>API Keys</CardTitle>
                <p className="text-[11px] text-text-tertiary mt-0.5">Telemetry ingestion keys</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: "Production Key", value: "otw_prod_****7x9k" },
                { label: "Development Key", value: "otw_dev_****3m2p" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <span className="text-xs text-text-secondary">{item.label}</span>
                  <code className="text-xs font-mono text-text-tertiary bg-bg-400 px-2 py-0.5 rounded">{item.value}</code>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button variant="ghost" onClick={() => router.back()}>Cancel</Button>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : saved ? "Saved ✓" : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
