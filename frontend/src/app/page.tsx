"use client";

import { useState, useCallback, useEffect } from "react";
import type { AirportNotes, BriefingData } from "@/lib/types";
import BriefingView from "@/components/BriefingView";
import { generateTextBriefing } from "@/lib/textBriefing";

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }

  if (typeof window !== "undefined" && window.location.hostname === "localhost") {
    return "http://localhost:8000";
  }

  return "";
}

async function fetchAirportNotes(
  briefing: BriefingData,
): Promise<AirportNotes | null> {
  const params = new URLSearchParams({
    departure: briefing.flight_info.departure_icao,
    arrival: briefing.flight_info.arrival_icao,
  });

  const res = await fetch(`${getApiBase()}/api/airport-notes?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Airport notes lookup failed: ${res.status}`);
  }

  return (await res.json()) as AirportNotes | null;
}

export default function Home() {
  const [briefing, setBriefing] = useState<BriefingData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [copied, setCopied] = useState(false);
  const [hasSaved, setHasSaved] = useState(false);

  useEffect(() => {
    const saved = !!localStorage.getItem("lastBriefing");
    const timer = window.setTimeout(() => setHasSaved(saved), 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!briefing || briefing.airport_notes) return;

    let cancelled = false;

    void (async () => {
      try {
        const airportNotes = await fetchAirportNotes(briefing);
        if (!airportNotes || cancelled) return;

        const updatedBriefing: BriefingData = {
          ...briefing,
          airport_notes: airportNotes,
        };

        setBriefing(updatedBriefing);
        try {
          localStorage.setItem("lastBriefing", JSON.stringify(updatedBriefing));
        } catch {}
      } catch {
        // Saved briefings from older builds simply stay without notes if lookup fails.
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [briefing]);

  const copyToClipboard = useCallback(() => {
    if (!briefing) return;
    const text = generateTextBriefing(briefing);
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [briefing]);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${getApiBase()}/api/parse`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Parse failed" }));
        throw new Error(err.error || `Server error: ${res.status}`);
      }
      const data: BriefingData = await res.json();
      setBriefing(data);
      try { localStorage.setItem("lastBriefing", JSON.stringify(data)); } catch {}
      setHasSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  if (briefing) {
    return (
      <div className="min-h-screen">
        <div className="no-print flex flex-wrap items-center justify-between gap-2 px-4 sm:px-6 py-3 bg-surface border-b border-border">
          <h1 className="text-accent-green font-bold text-lg">FLIGHT PREP</h1>
          <div className="flex gap-2 sm:gap-3">
            <button
              onClick={copyToClipboard}
              className="px-3 sm:px-4 py-1.5 text-xs sm:text-sm bg-surface-2 border border-border rounded hover:bg-border transition-colors"
            >
              {copied ? "Copied!" : "Copy Text"}
            </button>
            <button
              onClick={() => window.print()}
              className="px-3 sm:px-4 py-1.5 text-xs sm:text-sm bg-surface-2 border border-border rounded hover:bg-border transition-colors"
            >
              Export PDF
            </button>
            <button
              onClick={() => {
                setBriefing(null);
                setError(null);
              }}
              className="px-3 sm:px-4 py-1.5 text-xs sm:text-sm bg-surface-2 border border-border rounded hover:bg-border transition-colors"
            >
              New
            </button>
          </div>
        </div>
        <BriefingView data={briefing} />
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-lg w-full text-center">
        <h1 className="text-accent-green font-bold text-3xl mb-2">
          FLIGHT PREP
        </h1>
        <p className="text-muted text-sm mb-8">
          Upload OFP PDF for cockpit-ready briefing
        </p>

        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          className={`block border-2 border-dashed rounded-lg p-12 cursor-pointer transition-colors ${
            dragOver
              ? "border-accent-green bg-accent-green/5"
              : "border-border hover:border-muted"
          }`}
        >
          {loading ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
              <p className="text-muted text-sm">Parsing OFP...</p>
            </div>
          ) : (
            <>
              <div className="text-4xl mb-4 opacity-40">
                {"✈"}
              </div>
              <p className="text-foreground mb-1">
                Drop OFP PDF here
              </p>
              <p className="text-muted text-sm">or click to select</p>
              <input
                type="file"
                accept=".pdf"
                onChange={onFileSelect}
                className="hidden"
              />
            </>
          )}
        </label>

        {hasSaved && (
          <button
            onClick={() => {
              try {
                const saved = localStorage.getItem("lastBriefing");
                if (saved) setBriefing(JSON.parse(saved));
              } catch {}
            }}
            className="mt-4 px-4 py-2 text-sm text-accent-green border border-accent-green/30 rounded hover:bg-accent-green/10 transition-colors"
          >
            Load Last Briefing
          </button>
        )}

        {error && (
          <p className="mt-4 text-accent-red text-sm">{error}</p>
        )}
      </div>
    </div>
  );
}
