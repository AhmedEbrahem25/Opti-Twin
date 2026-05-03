/**
 * SavedSearchBanner — slim row that polls the canonical default saved search
 * ("safety overrides this shift") every 30s and renders the count.
 *
 * Mute is purely client-side via localStorage; muted state still polls but
 * renders compactly until the timestamp expires.
 */

import { useCallback, useEffect, useState } from "react";
import {
  type SavedSearchDefault,
  getDefaultSavedSearch,
  searchOpti,
} from "../../lib/search";

const MUTE_KEY = "opti.searchBanner.muteUntil";
const POLL_MS = 30_000;

type Props = {
  /** Called when the user clicks "view all" to jump to the palette. */
  onOpenPalette?: () => void;
};

export default function SavedSearchBanner({ onOpenPalette }: Props) {
  const [saved, setSaved] = useState<SavedSearchDefault | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const [muteUntil, setMuteUntil] = useState<number>(() => {
    if (typeof window === "undefined") return 0;
    const v = localStorage.getItem(MUTE_KEY);
    return v ? parseInt(v, 10) : 0;
  });

  const isMuted = Date.now() < muteUntil;

  const poll = useCallback(async (preset: SavedSearchDefault) => {
    try {
      const resp = await searchOpti("", { ...preset.query, limit: 1 });
      setCount(resp.total);
    } catch {
      setCount(null);
    }
  }, []);

  // Load preset once + poll loop.
  useEffect(() => {
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | null = null;

    (async () => {
      try {
        const preset = await getDefaultSavedSearch();
        if (cancelled) return;
        setSaved(preset);
        await poll(preset);
        interval = setInterval(() => poll(preset), POLL_MS);
      } catch {
        // banner stays hidden if the saved-search endpoint isn't available
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

  if (!saved || count === null) return null;

  // Muted — render a slim "click to unmute" pill instead.
  if (isMuted) {
    return (
      <div className="mb-2 flex items-center justify-end gap-3 text-[11px] text-steel-100/40">
        <span>🔕 Banner muted until {new Date(muteUntil).toLocaleTimeString()}</span>
        <button
          onClick={handleUnmute}
          className="rounded bg-steel-700/40 px-2 py-0.5 hover:bg-steel-700/70"
        >
          Unmute
        </button>
      </div>
    );
  }

  const tone =
    count === 0 ? "border-steel-500/30 bg-steel-800/40 text-steel-100/70"
    : count <= 2 ? "border-flame-500/40 bg-flame-500/10 text-flame-200"
    : "border-red-500/40 bg-red-500/10 text-red-200";

  return (
    <div
      className={`mb-3 flex items-center justify-between rounded-lg border px-4 py-2 text-sm ${tone}`}
    >
      <div className="flex items-center gap-3">
        <span className="text-base">🔔</span>
        <span>
          <strong>{count}</strong>{" "}
          {saved.title_en.toLowerCase()}{" "}
          {count === 1 ? "logged" : "logged"}.
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <button
          onClick={onOpenPalette}
          className="rounded bg-steel-700/40 px-2 py-1 hover:bg-steel-700/70"
        >
          View all
        </button>
        <button
          onClick={handleMute}
          className="rounded bg-steel-700/40 px-2 py-1 hover:bg-steel-700/70"
        >
          Mute 1h
        </button>
      </div>
    </div>
  );
}
