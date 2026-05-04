/**
 * SavedSearchBanner — slim row that polls the canonical default saved search
 * ("safety overrides this shift") every 30s and renders the count.
 *
 * Mute is purely client-side via localStorage; muted state still polls but
 * renders compactly until the timestamp expires. Language toggle (EN/AR)
 * is also persisted to localStorage.
 */

import { useCallback, useEffect, useState } from "react";
import {
  type SavedSearchDefault,
  getDefaultSavedSearch,
  searchOpti,
} from "../../lib/search";

const MUTE_KEY = "opti.searchBanner.muteUntil";
const LANG_KEY = "opti.searchBanner.lang";
const POLL_MS = 30_000;

type Lang = "en" | "ar";

type Props = {
  onOpenPalette?: () => void;
};

const COPY: Record<Lang, { event: string; events: string; viewAll: string; mute: string; unmute: string; offline: string; mutedSuffix: string }> = {
  en: {
    event: "event",
    events: "events",
    viewAll: "View all",
    mute: "Mute 1h",
    unmute: "Unmute",
    offline: "Saved-search offline — backend unreachable",
    mutedSuffix: "Banner muted until",
  },
  ar: {
    event: "حدث",
    events: "أحداث",
    viewAll: "عرض الكل",
    mute: "كتم لساعة",
    unmute: "إلغاء الكتم",
    offline: "البحث المحفوظ غير متاح — الخادم غير متصل",
    mutedSuffix: "كتم البانر حتى",
  },
};

export default function SavedSearchBanner({ onOpenPalette }: Props) {
  const [saved, setSaved] = useState<SavedSearchDefault | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [failed, setFailed] = useState(false);
  const [muteUntil, setMuteUntil] = useState<number>(() => {
    if (typeof window === "undefined") return 0;
    const v = localStorage.getItem(MUTE_KEY);
    return v ? parseInt(v, 10) : 0;
  });
  const [lang, setLang] = useState<Lang>(() => {
    if (typeof window === "undefined") return "en";
    return localStorage.getItem(LANG_KEY) === "ar" ? "ar" : "en";
  });

  const isMuted = Date.now() < muteUntil;
  const t = COPY[lang];

  const poll = useCallback(async (preset: SavedSearchDefault) => {
    try {
      const resp = await searchOpti("", { ...preset.query, limit: 1 });
      setCount(resp.total);
      setFailed(false);
    } catch {
      setCount(null);
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | null = null;

    (async () => {
      try {
        const preset = await getDefaultSavedSearch();
        if (cancelled) return;
        setSaved(preset);
        setFailed(false);
        await poll(preset);
        interval = setInterval(() => poll(preset), POLL_MS);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();

    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [poll]);

  const handleMute = useCallback(() => {
    const until = Date.now() + 60 * 60 * 1000;
    localStorage.setItem(MUTE_KEY, String(until));
    setMuteUntil(until);
  }, []);

  const handleUnmute = useCallback(() => {
    localStorage.removeItem(MUTE_KEY);
    setMuteUntil(0);
  }, []);

  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const next: Lang = prev === "en" ? "ar" : "en";
      localStorage.setItem(LANG_KEY, next);
      return next;
    });
  }, []);

  // Soft-fail strip — surfaces the absence rather than silently hiding.
  if (failed && !saved) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="mb-2 flex items-center justify-end text-[11px] text-steel-100/40"
      >
        <span>⚠ {t.offline}</span>
      </div>
    );
  }

  if (!saved || count === null) return null;

  if (isMuted) {
    return (
      <div className="mb-2 flex items-center justify-end gap-3 text-[11px] text-steel-100/40">
        <span>🔕 {t.mutedSuffix} {new Date(muteUntil).toLocaleTimeString()}</span>
        <button
          onClick={handleUnmute}
          aria-label={t.unmute}
          className="rounded bg-steel-700/40 px-2 py-0.5 hover:bg-steel-700/70"
        >
          {t.unmute}
        </button>
      </div>
    );
  }

  const tone =
    count === 0 ? "border-steel-500/30 bg-steel-800/40 text-steel-100/70"
    : count <= 2 ? "border-flame-500/40 bg-flame-500/10 text-flame-200"
    : "border-red-500/40 bg-red-500/10 text-red-200";

  const title = lang === "ar" ? saved.title_ar || saved.title_en : saved.title_en;
  const noun = count === 1 ? t.event : t.events;
  const dir = lang === "ar" ? "rtl" : "ltr";

  return (
    <div
      role="status"
      aria-live="polite"
      dir={dir}
      className={`mb-3 flex items-center justify-between rounded-lg border px-4 py-2 text-sm ${tone}`}
    >
      <div className="flex items-center gap-3">
        <span className="text-base" aria-hidden="true">🔔</span>
        <span>
          <strong key={count} className="opti-count-pop">{count}</strong>{" "}
          {title}{" "}
          {lang === "en" ? `${noun} logged.` : `(${noun}).`}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs" dir="ltr">
        <button
          onClick={toggleLang}
          aria-label="Toggle language"
          title="EN / AR"
          className="rounded bg-steel-700/40 px-2 py-1 text-[10px] uppercase tracking-wide hover:bg-steel-700/70"
        >
          {lang === "en" ? "AR" : "EN"}
        </button>
        <button
          onClick={onOpenPalette}
          className="rounded bg-steel-700/40 px-2 py-1 hover:bg-steel-700/70"
        >
          {t.viewAll}
        </button>
        <button
          onClick={handleMute}
          aria-label={t.mute}
          className="rounded bg-steel-700/40 px-2 py-1 hover:bg-steel-700/70"
        >
          {t.mute}
        </button>
      </div>
    </div>
  );
}
