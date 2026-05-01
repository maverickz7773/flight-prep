"use client";

import { useState, useCallback } from "react";
import type {
  WeatherData,
  NOTAMData,
  AirportWeather,
  NOTAMItem,
  FIRWeatherBlock,
  FIRNotamBlock,
  AirportNotamBlock,
} from "@/lib/types";
import Section from "../Section";

function HighlightWx({ text }: { text: string }) {
  const parts = text.split(/(TEMPO\s+[^\s]+\s+.*?)(?=\s+TEMPO|\s+BECMG|\s+PROB|$)/g);
  return (
    <>
      {parts.map((part, i) => {
        const isThreat = /TSRA|TS\s|CB|FEW\d+CB/.test(part) && /TEMPO/.test(part);
        return (
          <span key={i} className={isThreat ? "text-accent-amber font-bold" : ""}>
            {part}
          </span>
        );
      })}
    </>
  );
}

function NotamItemRow({ notam }: { notam: NOTAMItem }) {
  const [expanded, setExpanded] = useState(false);
  const color =
    notam.relevance === "HIGH"
      ? "text-accent-red"
      : notam.relevance === "MEDIUM"
        ? "text-accent-amber"
        : "text-muted";

  return (
    <div className="mb-0.5">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-left w-full text-xs flex items-start gap-1 hover:bg-surface-2 rounded px-1 -mx-1"
      >
        <span className={`${color} font-bold shrink-0 w-4`}>
          {notam.relevance === "HIGH" ? "!" : notam.relevance === "MEDIUM" ? "~" : "."}
        </span>
        <span className="text-muted shrink-0 w-20">{notam.reference}</span>
        <span className="text-foreground flex-1 truncate">
          {notam.summary || notam.text.slice(0, 80)}
        </span>
        <span className="text-muted shrink-0 no-print">{expanded ? "▼" : "▶"}</span>
      </button>
      {expanded && (
        <pre className="text-xs text-muted ml-6 mt-0.5 whitespace-pre-wrap max-h-40 overflow-y-auto">
          {notam.text}
        </pre>
      )}
    </div>
  );
}

function NotamList({
  notams,
  showLow,
}: {
  notams: NOTAMItem[];
  showLow: boolean;
}) {
  const filtered = showLow ? notams : notams.filter((n) => n.relevance !== "LOW");
  if (filtered.length === 0) return null;

  return (
    <div className="mt-1 ml-2">
      <p className="text-xs text-muted mb-0.5">NOTAMs ({filtered.length})</p>
      {filtered.map((n, i) => (
        <NotamItemRow key={i} notam={n} />
      ))}
    </div>
  );
}

function AirportBlock({
  label,
  wx,
  notams,
  showLow,
  expectedTime,
}: {
  label?: string;
  wx: AirportWeather | null;
  notams: NOTAMItem[];
  showLow: boolean;
  expectedTime?: string;
}) {
  if (!wx && notams.length === 0) return null;

  const icao = wx?.icao ?? "";
  const hasCB =
    (wx?.metar && /CB|TS|TSRA/i.test(wx.metar)) ||
    (wx?.taf && /CB|TS|TSRA/i.test(wx.taf));

  const highCount = notams.filter((n) => n.relevance === "HIGH").length;

  return (
    <div className="mb-3 pl-2 border-l-2 border-border">
      <p className="text-xs font-bold mb-0.5">
        {label && <span className="text-muted">{label}: </span>}
        <span className={hasCB ? "text-accent-amber" : "text-accent-green"}>
          {icao}
        </span>
        {wx?.name && <span className="text-muted font-normal ml-1">{wx.name}</span>}
        {expectedTime && (
          <span className="text-muted font-normal ml-2 tabular-nums">{expectedTime}</span>
        )}
        {hasCB && <span className="text-accent-amber ml-1">CB/TS</span>}
        {highCount > 0 && (
          <span className="text-accent-red font-normal ml-2 text-xs">
            {highCount} critical NOTAM{highCount > 1 ? "s" : ""}
          </span>
        )}
      </p>

      {wx?.metar && (
        <p className="text-xs text-foreground ml-2">
          <span className="text-muted">METAR: </span>
          {wx.metar}
        </p>
      )}
      {wx?.taf && (
        <p className="text-xs text-foreground ml-2 break-all">
          <span className="text-muted">TAF: </span>
          <HighlightWx text={wx.taf} />
        </p>
      )}

      <NotamList notams={notams} showLow={showLow} />
    </div>
  );
}

function EnrouteFIRBlock({
  wxBlock,
  notamBlock,
  enrouteAirportNotams,
  showLow,
  airportTimes,
}: {
  wxBlock: FIRWeatherBlock | null;
  notamBlock: FIRNotamBlock | null;
  enrouteAirportNotams: AirportNotamBlock[];
  showLow: boolean;
  airportTimes: Record<string, string>;
}) {
  const fir_icao = wxBlock?.fir_icao ?? notamBlock?.fir_icao ?? "";
  const fir_name = wxBlock?.fir_name ?? notamBlock?.fir_name ?? "";

  return (
    <div className="mb-2 pl-2 border-l-2 border-border">
      <p className="text-xs font-bold text-accent-green mb-0.5">
        {fir_name} ({fir_icao})
      </p>
      {wxBlock?.sigmets.map((s, i) => (
        <p key={i} className="text-xs text-accent-amber ml-2 mb-0.5">
          SIGMET: {s.phenomenon || "WX"} {s.top && `TOP ${s.top}`}
        </p>
      ))}

      {notamBlock && notamBlock.notams.length > 0 && (
        <NotamList notams={notamBlock.notams} showLow={showLow} />
      )}

      {wxBlock?.airports.map((a, i) => {
        const airportNotamBlock = enrouteAirportNotams.find(
          (nb) => nb.icao === a.icao
        );
        return (
          <AirportBlock
            key={i}
            wx={a}
            notams={airportNotamBlock?.notams ?? []}
            showLow={showLow}
            expectedTime={airportTimes[a.icao]}
          />
        );
      })}
    </div>
  );
}

export default function WxNotamSection({
  weather,
  notams,
  enrouteAirportList,
  airportTimes,
}: {
  weather: WeatherData;
  notams: NOTAMData;
  enrouteAirportList: string[];
  airportTimes: Record<string, string>;
}) {
  const [showLow, setShowLow] = useState(false);
  const [showEnroute, setShowEnroute] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyAirportList = useCallback(() => {
    const text = enrouteAirportList.join(" ");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [enrouteAirportList]);

  const allFirKeys = new Set<string>();
  weather.enroute.forEach((b) => allFirKeys.add(b.fir_icao));
  notams.enroute.forEach((b) => allFirKeys.add(b.fir_icao));

  const enrouteCount = allFirKeys.size;
  const sigmetCount = weather.enroute.reduce((n, b) => n + b.sigmets.length, 0);

  return (
    <Section number={7} title="WEATHER & NOTAMS">
      <div className="flex gap-4 mb-2 no-print">
        <label className="text-xs text-muted flex items-center gap-1">
          <input
            type="checkbox"
            checked={showLow}
            onChange={(e) => setShowLow(e.target.checked)}
            className="accent-accent-green"
          />
          Show LOW relevance
        </label>
      </div>

      <AirportBlock
        label="DEPARTURE"
        wx={weather.departure}
        notams={notams.departure}
        showLow={showLow}
        expectedTime={weather.departure ? airportTimes[weather.departure.icao] : undefined}
      />
      <AirportBlock
        label="DESTINATION"
        wx={weather.destination}
        notams={notams.destination}
        showLow={showLow}
        expectedTime={weather.destination ? airportTimes[weather.destination.icao] : undefined}
      />

      {weather.alternates.length > 0 && (
        <div className="mb-2">
          <p className="text-xs font-bold text-muted mb-0.5">ALTERNATES</p>
          {weather.alternates.map((a, i) => {
            const altNotamBlock = notams.alternates.find(
              (nb) => nb.icao === a.icao
            );
            return (
              <AirportBlock
                key={i}
                wx={a}
                notams={altNotamBlock?.notams ?? []}
                showLow={showLow}
                expectedTime={airportTimes[a.icao]}
              />
            );
          })}
        </div>
      )}

      {enrouteAirportList.length > 0 && (
        <div className="mb-3 p-2 bg-surface-2 rounded border border-border">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-bold text-muted">
              ENROUTE AIRPORTS ({enrouteAirportList.length})
            </p>
            <button
              onClick={copyAirportList}
              className="text-xs px-2 py-0.5 bg-surface border border-border rounded hover:bg-border transition-colors no-print"
            >
              {copied ? "Copied!" : "Copy for Jepps FD Pro"}
            </button>
          </div>
          <p className="text-xs text-foreground font-mono">
            {enrouteAirportList.join("  ")}
          </p>
        </div>
      )}

      {enrouteCount > 0 && (
        <div>
          <button
            onClick={() => setShowEnroute(!showEnroute)}
            className="text-xs text-accent-green hover:underline mb-1 no-print"
          >
            {showEnroute ? "▼" : "▶"} ENROUTE BY FIR ({enrouteCount} FIRs
            {sigmetCount > 0 && `, ${sigmetCount} SIGMETs`})
          </button>
          <div className="print-show">
            {(showEnroute || typeof window === "undefined") &&
              Array.from(allFirKeys).map((firIcao) => {
                const wxBlock = weather.enroute.find((b) => b.fir_icao === firIcao) ?? null;
                const notamBlock = notams.enroute.find((b) => b.fir_icao === firIcao) ?? null;
                return (
                  <EnrouteFIRBlock
                    key={firIcao}
                    wxBlock={wxBlock}
                    notamBlock={notamBlock}
                    enrouteAirportNotams={notams.enroute_airports}
                    showLow={showLow}
                    airportTimes={airportTimes}
                  />
                );
              })}
          </div>
        </div>
      )}
    </Section>
  );
}
