"use client";

import { useState } from "react";

import type { AirportFeedbackEntry } from "@/lib/types";

type FeedbackSection = "departure" | "arrival";

type FeedbackPayload = {
  section: FeedbackSection;
  airport_icao: string;
  flight_date: string;
  route_text: string | null;
  from_icao: string;
  to_icao: string;
  sid: string | null;
  star: string | null;
  runway: string | null;
  approach_runway: string | null;
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

function defaultRouteText(fromIcao: string, toIcao: string): string {
  return `${fromIcao} → ${toIcao}`;
}

export default function AirportFeedbackPanel({
  title = "FLIGHT HISTORY",
  section,
  airportIcao,
  flightDate,
  fromIcao,
  toIcao,
  sid = null,
  star = null,
  runway = null,
  initialEntries,
}: {
  title?: string;
  section: FeedbackSection;
  airportIcao: string;
  flightDate: string;
  fromIcao: string;
  toIcao: string;
  sid?: string | null;
  star?: string | null;
  runway?: string | null;
  initialEntries: AirportFeedbackEntry[];
}) {
  const [entries, setEntries] = useState<AirportFeedbackEntry[]>(initialEntries);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [departureDate, setDepartureDate] = useState(flightDate);
  const [departureRoute, setDepartureRoute] = useState(defaultRouteText(fromIcao, toIcao));
  const [departureSid, setDepartureSid] = useState(sid ?? "");
  const [departureRunway, setDepartureRunway] = useState(runway ?? "");
  const [arrivalDate, setArrivalDate] = useState(flightDate);
  const [arrivalRoute, setArrivalRoute] = useState(defaultRouteText(fromIcao, toIcao));
  const [arrivalStar, setArrivalStar] = useState(star ?? "");
  const [arrivalRunway, setArrivalRunway] = useState(runway ?? "");
  const [comments, setComments] = useState("");

  async function handleSave() {
    if (!comments.trim()) {
      setError("Comments are required");
      return;
    }

    const payload: FeedbackPayload =
      section === "departure"
        ? {
            section,
            airport_icao: airportIcao,
            flight_date: departureDate.trim(),
            route_text: departureRoute.trim() || defaultRouteText(fromIcao, toIcao),
            from_icao: fromIcao,
            to_icao: toIcao,
            sid: departureSid.trim() || null,
            star: null,
            runway: departureRunway.trim() || null,
            approach_runway: null,
            comments: comments.trim(),
          }
        : {
            section,
            airport_icao: airportIcao,
            flight_date: arrivalDate.trim(),
            route_text: arrivalRoute.trim() || defaultRouteText(fromIcao, toIcao),
            from_icao: fromIcao,
            to_icao: toIcao,
            sid: null,
            star: arrivalStar.trim() || null,
            runway: arrivalRunway.trim() || null,
            approach_runway: arrivalRunway.trim() || null,
            comments: comments.trim(),
          };

    setSaving(true);
    setError(null);

    try {
      const res = await fetch("/api/airport-feedback", {
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

      const created = (await res.json()) as AirportFeedbackEntry;
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

  async function handleDelete(entry: AirportFeedbackEntry) {
    const preview = entry.comments.length > 80 ? `${entry.comments.slice(0, 80)}...` : entry.comments;
    const confirmed = window.confirm(
      `Delete this feedback entry?\n\nDate: ${entry.flight_date}\nComment: ${preview}`,
    );
    if (!confirmed) return;

    try {
      const res = await fetch(`/api/airport-feedback/${entry.id}`, {
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

  function renderDepartureForm() {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-xs">
        <div>
          <label className="block text-muted mb-1">Date</label>
          <input
            value={departureDate}
            onChange={(e) => setDepartureDate(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
        <div>
          <label className="block text-muted mb-1">SID</label>
          <input
            value={departureSid}
            onChange={(e) => setDepartureSid(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
        <div className="sm:col-span-2">
          <label className="block text-muted mb-1">Route</label>
          <input
            value={departureRoute}
            onChange={(e) => setDepartureRoute(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
        <div>
          <label className="block text-muted mb-1">Runway</label>
          <input
            value={departureRunway}
            onChange={(e) => setDepartureRunway(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
      </div>
    );
  }

  function renderArrivalForm() {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-xs">
        <div>
          <label className="block text-muted mb-1">Date</label>
          <input
            value={arrivalDate}
            onChange={(e) => setArrivalDate(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
        <div>
          <label className="block text-muted mb-1">STAR</label>
          <input
            value={arrivalStar}
            onChange={(e) => setArrivalStar(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
        <div className="sm:col-span-2">
          <label className="block text-muted mb-1">Route</label>
          <input
            value={arrivalRoute}
            onChange={(e) => setArrivalRoute(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
        <div>
          <label className="block text-muted mb-1">Runway</label>
          <input
            value={arrivalRunway}
            onChange={(e) => setArrivalRunway(e.target.value)}
            className="w-full rounded border border-border bg-surface px-2 py-1 text-foreground outline-none focus:border-accent-green"
          />
        </div>
      </div>
    );
  }

  function renderEntryDetails(entry: AirportFeedbackEntry) {
    if (section === "departure") {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
          <div className="flex gap-2">
            <span className="text-muted shrink-0">Date</span>
            <span className="text-foreground">{entry.flight_date}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted shrink-0">SID</span>
            <span className="text-foreground">{entry.sid || "N/A"}</span>
          </div>
          <div className="flex gap-2 sm:col-span-2">
            <span className="text-muted shrink-0">Route</span>
            <span className="text-foreground">
              {entry.route_text || defaultRouteText(entry.from_icao, entry.to_icao)}
            </span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted shrink-0">Runway</span>
            <span className="text-foreground">{entry.runway || "N/A"}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-muted shrink-0">Saved</span>
            <span className="text-foreground">{formatCreatedAt(entry.created_at)}</span>
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
        <div className="flex gap-2">
          <span className="text-muted shrink-0">Date</span>
          <span className="text-foreground">{entry.flight_date}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-muted shrink-0">STAR</span>
          <span className="text-foreground">{entry.star || "N/A"}</span>
        </div>
        <div className="flex gap-2 sm:col-span-2">
          <span className="text-muted shrink-0">Route</span>
          <span className="text-foreground">
            {entry.route_text || defaultRouteText(entry.from_icao, entry.to_icao)}
          </span>
        </div>
        <div className="flex gap-2">
          <span className="text-muted shrink-0">Runway</span>
          <span className="text-foreground">{entry.runway || "N/A"}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-muted shrink-0">Saved</span>
          <span className="text-foreground">{formatCreatedAt(entry.created_at)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-3 pt-3 border-t border-border">
      <div className="flex items-center justify-between gap-3 mb-2">
        <p className="text-accent-green text-[11px] font-bold">{title}</p>
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
        <div className="mb-3 rounded border border-accent-green/20 bg-accent-green/5 px-3 py-2 space-y-2">
          {section === "departure" ? renderDepartureForm() : renderArrivalForm()}

          <div>
            <label className="block text-[11px] text-muted mb-1">Comments</label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="w-full min-h-24 rounded border border-border bg-surface px-2 py-1 text-xs text-foreground outline-none focus:border-accent-green"
              placeholder="Add operational feedback for this airport"
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
              <div key={entry.id} className="rounded border border-border bg-surface-2 px-3 py-2">
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
                    {renderEntryDetails(entry)}
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
  );
}
