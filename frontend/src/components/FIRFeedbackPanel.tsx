"use client";

import { useEffect, useState } from "react";

import type { FIRFeedbackEntry } from "@/lib/types";
import InlineDisclosure from "./InlineDisclosure";

type FIRFeedbackPayload = {
  fir_icao: string;
  fir_name: string;
  flight_date: string;
  route_text: string;
  from_icao: string;
  to_icao: string;
  comments: string;
};

function formatCreatedAt(createdAt: string): string {
  const parsed = new Date(createdAt);
  if (Number.isNaN(parsed.getTime())) {
    return createdAt;
  }
  return parsed.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function FIRFeedbackPanel({
  firIcao,
  firName,
  flightDate,
  fromIcao,
  toIcao,
  routeText,
  initialEntries,
}: {
  firIcao: string;
  firName: string;
  flightDate: string;
  fromIcao: string;
  toIcao: string;
  routeText: string;
  initialEntries: FIRFeedbackEntry[];
}) {
  const [entries, setEntries] = useState<FIRFeedbackEntry[]>(initialEntries);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comments, setComments] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function refreshEntries() {
      try {
        const params = new URLSearchParams({
          firs: firIcao,
        });
        const res = await fetch(`/api/fir-feedback?${params.toString()}`);
        if (!res.ok) return;

        const payload = (await res.json()) as Record<string, FIRFeedbackEntry[]> | null;
        if (cancelled || !payload) return;

        const latestEntries = payload[firIcao] ?? [];
        setEntries(latestEntries);
        setExpandedId((current) =>
          current != null && latestEntries.some((entry) => entry.id === current) ? current : null
        );
      } catch {
        // Keep the latest local entries if refresh fails.
      }
    }

    void refreshEntries();

    return () => {
      cancelled = true;
    };
  }, [firIcao]);

  async function handleSave() {
    if (!comments.trim()) {
      setError("Comments are required");
      return;
    }

    const payload: FIRFeedbackPayload = {
      fir_icao: firIcao,
      fir_name: firName,
      flight_date: flightDate,
      route_text: routeText.trim(),
      from_icao: fromIcao,
      to_icao: toIcao,
      comments: comments.trim(),
    };

    setSaving(true);
    setError(null);

    try {
      const res = await fetch("/api/fir-feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        const message =
          detail && typeof detail === "object" && "detail" in detail && typeof detail.detail === "string"
            ? detail.detail
            : "Failed to save feedback";
        throw new Error(message);
      }

      const created = (await res.json()) as FIRFeedbackEntry;
      setEntries((prev) => [created, ...prev]);
      setExpandedId(created.id);
      setComments("");
      setFormOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save feedback");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(entry: FIRFeedbackEntry) {
    const preview = entry.comments.length > 80 ? `${entry.comments.slice(0, 80)}...` : entry.comments;
    const confirmed = window.confirm(
      `Delete this feedback entry?\n\nDate: ${entry.flight_date}\nComment: ${preview}`,
    );
    if (!confirmed) return;

    try {
      const res = await fetch(`/api/fir-feedback/${entry.id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        const message =
          detail && typeof detail === "object" && "detail" in detail && typeof detail.detail === "string"
            ? detail.detail
            : "Failed to delete feedback";
        throw new Error(message);
      }
      setEntries((prev) => prev.filter((item) => item.id !== entry.id));
      if (expandedId === entry.id) {
        setExpandedId(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete feedback");
    }
  }

  const defaultOpen = entries.length > 0;

  return (
    <InlineDisclosure title="FLIGHT HISTORY" defaultOpen={defaultOpen}>
      <div className="space-y-2">
        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={() => {
              setFormOpen((prev) => !prev);
              setError(null);
            }}
            className="text-[11px] text-accent-green font-bold hover:text-foreground transition-colors"
          >
            {formOpen ? "Cancel" : "Add Feedback"}
          </button>
        </div>

        {formOpen && (
          <div className="rounded border border-accent-green/20 bg-accent-green/5 px-3 py-2 space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-xs">
              <div className="flex gap-2">
                <span className="text-muted shrink-0">Date</span>
                <span className="text-foreground">{flightDate}</span>
              </div>
              <div className="flex gap-2 sm:col-span-2">
                <span className="text-muted shrink-0">Route</span>
                <span className="text-foreground">{routeText}</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] text-muted mb-1">Comments</label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                className="w-full min-h-24 rounded border border-border bg-surface px-2 py-1 text-xs text-foreground outline-none focus:border-accent-green"
                placeholder={`Add operational feedback for ${firIcao}`}
              />
            </div>

            {error && <p className="text-accent-red text-[11px]">{error}</p>}

            <div className="flex justify-end">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="px-3 py-1.5 text-[11px] bg-surface-2 border border-border rounded hover:bg-border transition-colors disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Feedback"}
              </button>
            </div>
          </div>
        )}

        {entries.length === 0 ? (
          <p className="text-xs text-muted">No feedback saved yet.</p>
        ) : (
          <div className="space-y-2">
            {entries.map((entry) => {
              const isOpen = expandedId === entry.id;
              return (
                <div key={entry.id} className="rounded border border-border bg-surface px-3 py-2">
                  <button
                    type="button"
                    onClick={() => setExpandedId(isOpen ? null : entry.id)}
                    className="w-full flex items-center justify-between gap-3 text-left"
                  >
                    <span className="flex flex-col gap-0.5">
                      <span className="text-xs font-bold text-foreground">{entry.flight_date}</span>
                      <span className="text-[11px] text-muted">
                        {entry.from_icao} {entry.to_icao}
                      </span>
                    </span>
                    <span className="text-[11px] text-muted">{isOpen ? "▼" : "▶"}</span>
                  </button>
                  {isOpen && (
                    <div className="mt-2 space-y-2 text-xs">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
                        <div className="flex gap-2">
                          <span className="text-muted shrink-0">Date</span>
                          <span className="text-foreground">{entry.flight_date}</span>
                        </div>
                        <div className="flex gap-2">
                          <span className="text-muted shrink-0">Saved</span>
                          <span className="text-foreground">{formatCreatedAt(entry.created_at)}</span>
                        </div>
                        <div className="flex gap-2 sm:col-span-2">
                          <span className="text-muted shrink-0">Route</span>
                          <span className="text-foreground">{entry.route_text || `${entry.from_icao} → ${entry.to_icao}`}</span>
                        </div>
                      </div>
                      <p className="text-foreground whitespace-pre-line leading-relaxed">{entry.comments}</p>
                      <div className="flex justify-end">
                        <button
                          type="button"
                          onClick={() => void handleDelete(entry)}
                          className="text-[11px] font-bold text-accent-red hover:text-foreground transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </InlineDisclosure>
  );
}
