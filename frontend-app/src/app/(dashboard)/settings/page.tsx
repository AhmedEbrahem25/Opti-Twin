"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { User, Building2, Key, Bell, Brain, Shield, Palette, Globe } from "lucide-react";

const settingsSections = [
  {
    icon: Building2, title: "Organization", desc: "Manage your organization profile and billing",
    items: [
      { label: "Organization Name", value: "Alamein Manufacturing", type: "text" },
      { label: "Plan", value: "Enterprise", type: "badge" },
      { label: "Region", value: "Middle East (Cairo)", type: "text" },
    ],
  },
  {
    icon: User, title: "Account", desc: "Your personal account settings",
    items: [
      { label: "Name", value: "Ahmed Ibrahim", type: "text" },
      { label: "Email", value: "ahmed@alamein-mfg.com", type: "text" },
      { label: "Role", value: "Admin", type: "badge" },
    ],
  },
  {
    icon: Brain, title: "AI Configuration", desc: "Tune the AI agent's reward function weights",
    items: [
      { label: "Energy Weight (α)", value: "1.0", type: "number" },
      { label: "Machine Stress Weight (β)", value: "0.8", type: "number" },
      { label: "Production Delay Weight (γ)", value: "1.5", type: "number" },
      { label: "Decision Interval", value: "3 seconds", type: "text" },
    ],
  },
  {
    icon: Bell, title: "Notifications", desc: "Configure alert thresholds and notification channels",
    items: [
      { label: "Email Notifications", value: "Enabled", type: "badge" },
      { label: "Critical Alert SMS", value: "Enabled", type: "badge" },
      { label: "AI Decision Digest", value: "Hourly", type: "text" },
    ],
  },
  {
    icon: Key, title: "API Keys", desc: "Manage API keys for telemetry ingestion",
    items: [
      { label: "Production Key", value: "otw_prod_****7x9k", type: "mono" },
      { label: "Development Key", value: "otw_dev_****3m2p", type: "mono" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-xl font-bold text-text-primary font-[family-name:var(--font-display)] tracking-tight">Settings</h1>
        <p className="text-sm text-text-tertiary mt-0.5">Manage your workspace, AI configuration, and integrations</p>
      </div>

      <div className="space-y-4">
        {settingsSections.map((section) => (
          <Card key={section.title}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-bg-400 border border-border flex items-center justify-center">
                  <section.icon size={16} className="text-text-tertiary" />
                </div>
                <div>
                  <CardTitle>{section.title}</CardTitle>
                  <p className="text-[11px] text-text-tertiary mt-0.5">{section.desc}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {section.items.map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <span className="text-xs text-text-secondary">{item.label}</span>
                    {item.type === "badge" ? (
                      <Badge variant="accent" size="sm">{item.value}</Badge>
                    ) : item.type === "mono" ? (
                      <code className="text-xs font-mono text-text-tertiary bg-bg-400 px-2 py-0.5 rounded">{item.value}</code>
                    ) : item.type === "number" ? (
                      <Input type="number" defaultValue={item.value} className="w-20 h-7 text-xs text-right" />
                    ) : (
                      <span className="text-xs text-text-primary">{item.value}</span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button variant="ghost">Cancel</Button>
        <Button>Save Changes</Button>
      </div>
    </div>
  );
}
