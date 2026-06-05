"use client";

import { useState, useCallback, useEffect } from "react";
import type {
  AirportFeedback,
  AirportNotes,
  BriefingData,
  FIRFeedbackEntry,
  ParseJobStart,
  ParseJobStatus,
} from "@/lib/types";
import BriefingView from "@/components/BriefingView";
import { generateTextBriefing } from "@/lib/textBriefing";
import { APP_VERSION } from "@/lib/version";

const PARSE_POLL_INTERVAL_MS = 2000;
const PARSE_POLL_TIMEOUT_MS = 5 * 60 * 1000;

function getApiBase(): string {
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }

  if (typeof window !== "undefined" && window.location.hostname === "localhost") {
    return "http://localhost:8000";
  }

  return "";
}

function getErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object") {
    const detail = "detail" in payload ? payload.detail : undefined;
    if (typeof detail === "string") return detail;

    const error = "error" in payload ? payload.error : undefined;
    if (typeof error === "string") return error;
  }

  return fallback;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
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

async function fetchAirportFeedback(
  briefing: BriefingData,
): Promise<AirportFeedback | null> {
  const params = new URLSearchParams({
    departure: briefing.flight_info.departure_icao,
    arrival: briefing.flight_info.arrival_icao,
  });

  const res = await fetch(`${getApiBase()}/api/airport-feedback?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Airport feedback lookup failed: ${res.status}`);
  }

  return (await res.json()) as AirportFeedback | null;
}

async function fetchFirFeedback(
  briefing: BriefingData,
): Promise<Record<string, FIRFeedbackEntry[]>> {
  const firs = Array.from(
    new Set(
      (briefing.route.enroute_info ?? [])
        .map((item) => item.fir_icao)
        .filter((value): value is string => Boolean(value))
    )
  );

  if (firs.length === 0) {
    return {};
  }

  const params = new URLSearchParams({
    firs: firs.join(","),
  });

  const res = await fetch(`${getApiBase()}/api/fir-feedback?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`FIR feedback lookup failed: ${res.status}`);
  }

  return ((await res.json()) as Record<string, FIRFeedbackEntry[]> | null) ?? {};
}

export default function Home() {
  const [briefing, setBriefing] = useState<BriefingData | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("Parsing OFP...");
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
    if (!briefing) return;

    const needsAirportNotes = !briefing.airport_notes;

    let cancelled = false;

    void (async () => {
      try {
        const [airportNotes, airportFeedback, firFeedback] = await Promise.all([
          needsAirportNotes ? fetchAirportNotes(briefing) : Promise.resolve(briefing.airport_notes),
          fetchAirportFeedback(briefing),
          fetchFirFeedback(briefing),
        ]);
        if (cancelled) return;

        const currentFeedbackJson = JSON.stringify(briefing.airport_feedback ?? null);
        const fetchedFeedbackJson = JSON.stringify(airportFeedback);
        const currentFirFeedbackJson = JSON.stringify(briefing.route.fir_feedback ?? {});
        const fetchedFirFeedbackJson = JSON.stringify(firFeedback);
        const shouldUpdate =
          (needsAirportNotes && airportNotes !== briefing.airport_notes) ||
          fetchedFeedbackJson !== currentFeedbackJson ||
          fetchedFirFeedbackJson !== currentFirFeedbackJson;
        if (!shouldUpdate) return;

        const updatedBriefing: BriefingData = {
          ...briefing,
          airport_notes: airportNotes,
          airport_feedback: airportFeedback,
          route: {
            ...briefing.route,
            fir_feedback: firFeedback,
          },
        };

        setBriefing(updatedBriefing);
        try {
          localStorage.setItem("lastBriefing", JSON.stringify(updatedBriefing));
        } catch {}
      } catch {
        // Saved briefings from older builds simply stay without supplemental lookups if fetch fails.
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
    setLoadingMessage("Uploading OFP...");
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const createRes = await fetch(`${getApiBase()}/api/parse-jobs`, {
        method: "POST",
        body: formData,
      });
      if (!createRes.ok) {
        const err = await createRes.json().catch(() => ({ error: "Parse failed" }));
        throw new Error(getErrorMessage(err, `Server error: ${createRes.status}`));
      }

      const job: ParseJobStart = await createRes.json();
      const deadline = Date.now() + PARSE_POLL_TIMEOUT_MS;
      let completedData: BriefingData | null = null;

      setLoadingMessage("Parsing OFP on server...");

      while (Date.now() < deadline) {
        const statusRes = await fetch(`${getApiBase()}/api/parse-jobs/${job.job_id}`);
        if (!statusRes.ok) {
          const err = await statusRes.json().catch(() => ({ error: "Parse status check failed" }));
          throw new Error(getErrorMessage(err, `Server error: ${statusRes.status}`));
        }

        const status: ParseJobStatus = await statusRes.json();
        if (status.status === "completed" && status.result) {
          completedData = status.result;
          break;
        }

        if (status.status === "failed") {
          throw new Error(status.error || "Parse failed");
        }

        setLoadingMessage(
          status.status === "queued" ? "Queued for parsing..." : "Parsing OFP on server..."
        );
        await sleep(PARSE_POLL_INTERVAL_MS);
      }

      if (!completedData) {
        throw new Error("Parsing timed out. Please try again in a moment.");
      }

      setBriefing(completedData);
      const data = completedData;
      try { localStorage.setItem("lastBriefing", JSON.stringify(data)); } catch {}
      setHasSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
      setLoadingMessage("Parsing OFP...");
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
          <div className="flex items-baseline gap-2">
            <h1 className="text-accent-green font-bold text-lg">FLIGHT PREP</h1>
            <span className="text-[11px] sm:text-xs text-muted tracking-wide">
              {APP_VERSION}
            </span>
          </div>
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
          {APP_VERSION}
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
              <p className="text-muted text-sm">{loadingMessage}</p>
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
