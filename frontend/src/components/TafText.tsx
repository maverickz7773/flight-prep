"use client";

const PERIOD_RE = /\b(\d{4}\/\d{4})\b/;
const SPECIFIC_CLAUSE_RE =
  /\b(?:PROB\d{2}\s+TEMPO|PROB\d{2}|TEMPO|BECMG)\s+\d{4}\/\d{4}\b/g;
const MONTHS: Record<string, number> = {
  JAN: 0,
  FEB: 1,
  MAR: 2,
  APR: 3,
  MAY: 4,
  JUN: 5,
  JUL: 6,
  AUG: 7,
  SEP: 8,
  OCT: 9,
  NOV: 10,
  DEC: 11,
};

type TafClause = {
  start: number;
  end: number;
  period: string;
};

function parseFlightDate(date: string): Date | null {
  const match = date.match(/^(\d{2})([A-Za-z]{3})(\d{2})$/);
  if (!match) return null;

  const day = parseInt(match[1], 10);
  const month = MONTHS[match[2].toUpperCase()];
  const year = 2000 + parseInt(match[3], 10);
  if (month == null) return null;

  return new Date(Date.UTC(year, month, day, 0, 0, 0, 0));
}

function parseReferenceTime(referenceTime: string, flightDate: string): Date | null {
  const flightDateUtc = parseFlightDate(flightDate);
  if (!flightDateUtc) return null;

  const cleanedReference = referenceTime.trim().replace(/^~/, "").replace(/z$/i, "");
  const match = cleanedReference.match(/^(?:(\d{2})\/)?(\d{2})(\d{2})$/);
  if (!match) return null;

  const day = match[1] ? parseInt(match[1], 10) : flightDateUtc.getUTCDate();
  const hour = parseInt(match[2], 10);
  const minute = parseInt(match[3], 10);

  return new Date(
    Date.UTC(
      flightDateUtc.getUTCFullYear(),
      flightDateUtc.getUTCMonth(),
      day,
      hour,
      minute,
      0,
      0,
    ),
  );
}

function buildCandidateDate(anchor: Date, monthOffset: number, day: number, hour: number): Date {
  return new Date(
    Date.UTC(
      anchor.getUTCFullYear(),
      anchor.getUTCMonth() + monthOffset,
      day,
      hour,
      0,
      0,
      0,
    ),
  );
}

function closestDateForDayHour(anchor: Date, day: number, hour: number): Date {
  const candidates = [
    buildCandidateDate(anchor, -1, day, hour),
    buildCandidateDate(anchor, 0, day, hour),
    buildCandidateDate(anchor, 1, day, hour),
  ];

  return candidates.reduce((best, candidate) =>
    Math.abs(candidate.getTime() - anchor.getTime()) <
    Math.abs(best.getTime() - anchor.getTime())
      ? candidate
      : best,
  );
}

function nextDateForDayHour(anchor: Date, day: number, hour: number): Date {
  const candidates = [
    buildCandidateDate(anchor, -1, day, hour),
    buildCandidateDate(anchor, 0, day, hour),
    buildCandidateDate(anchor, 1, day, hour),
    buildCandidateDate(anchor, 2, day, hour),
  ].filter((candidate) => candidate.getTime() >= anchor.getTime());

  if (candidates.length === 0) {
    return buildCandidateDate(anchor, 1, day, hour);
  }

  return candidates.reduce((best, candidate) =>
    candidate.getTime() < best.getTime() ? candidate : best,
  );
}

function periodContainsReference(period: string, reference: Date): boolean {
  const match = period.match(/^(\d{2})(\d{2})\/(\d{2})(\d{2})$/);
  if (!match) return false;

  const startDay = parseInt(match[1], 10);
  const startHour = parseInt(match[2], 10);
  const endDay = parseInt(match[3], 10);
  const endHour = parseInt(match[4], 10);

  const start = closestDateForDayHour(reference, startDay, startHour);
  const end = nextDateForDayHour(start, endDay, endHour);

  return reference.getTime() >= start.getTime() && reference.getTime() <= end.getTime();
}

function getHighlightedClause(text: string, referenceTime: string, flightDate: string) {
  const reference = parseReferenceTime(referenceTime, flightDate);
  if (!reference) return null;

  const specificClauses: TafClause[] = [];
  for (const match of text.matchAll(SPECIFIC_CLAUSE_RE)) {
    const clauseText = match[0];
    const periodMatch = clauseText.match(PERIOD_RE);
    if (!periodMatch || match.index == null) continue;
    specificClauses.push({
      start: match.index,
      end: match.index + clauseText.length,
      period: periodMatch[1],
    });
  }

  for (let i = 0; i < specificClauses.length; i += 1) {
    const clause = specificClauses[i];
    const nextStart = specificClauses[i + 1]?.start ?? text.length;
    const fullClause = { ...clause, end: nextStart };
    if (periodContainsReference(fullClause.period, reference)) {
      return fullClause;
    }
  }

  const basePeriodMatch = PERIOD_RE.exec(text);
  if (!basePeriodMatch || basePeriodMatch.index == null) return null;

  const baseClauseEnd = specificClauses[0]?.start ?? text.length;
  const baseClause = {
    start: basePeriodMatch.index,
    end: baseClauseEnd,
    period: basePeriodMatch[1],
  };

  return periodContainsReference(baseClause.period, reference) ? baseClause : null;
}

export default function TafText({
  text,
  referenceTime,
  flightDate,
}: {
  text: string;
  referenceTime?: string;
  flightDate?: string;
}) {
  const highlightedClause =
    referenceTime && flightDate ? getHighlightedClause(text, referenceTime, flightDate) : null;

  if (!highlightedClause) {
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

  const before = text.slice(0, highlightedClause.start);
  const clause = text.slice(highlightedClause.start, highlightedClause.end);
  const after = text.slice(highlightedClause.end);
  const periodIndex = clause.indexOf(highlightedClause.period);
  const clauseBeforePeriod = periodIndex >= 0 ? clause.slice(0, periodIndex) : clause;
  const clauseAfterPeriod =
    periodIndex >= 0 ? clause.slice(periodIndex + highlightedClause.period.length) : "";

  return (
    <>
      {before}
      <span className="text-accent-amber">
        {clauseBeforePeriod}
        {periodIndex >= 0 ? (
          <span className="font-bold underline underline-offset-2">
            {highlightedClause.period}
          </span>
        ) : null}
        {clauseAfterPeriod}
      </span>
      {after}
    </>
  );
}
