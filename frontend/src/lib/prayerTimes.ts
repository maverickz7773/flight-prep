// Inflight prayer time calculator using the PrayTimes algorithm (praytimes.org)
// Configured for Umm Al-Qura method, Shafi'i Asr juristic

const DEG = Math.PI / 180;
const FAJR_ANGLE = 18.5; // Umm Al-Qura
const ISHA_MINUTES = 90; // Umm Al-Qura: 90 min after Maghrib
const EARTH_R = 6371000; // meters

export interface PrayerTimes {
  fajr: Date;
  sunrise: Date;
  dhuhr: Date;
  asr: Date;
  maghrib: Date;
  isha: Date;
}

function julianDate(year: number, month: number, day: number): number {
  if (month <= 2) {
    year -= 1;
    month += 12;
  }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + B - 1524.5;
}

function sunPosition(jd: number): { declination: number; equation: number } {
  const D = jd - 2451545.0;
  const g = ((357.529 + 0.98560028 * D) % 360) * DEG;
  const q = ((280.459 + 0.98564736 * D) % 360) * DEG;
  const L = q + (1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * DEG;
  const e = (23.439 - 0.00000036 * D) * DEG;
  const RA = Math.atan2(Math.cos(e) * Math.sin(L), Math.cos(L));
  const dec = Math.asin(Math.sin(e) * Math.sin(L));
  let eqt = (q / DEG / 15) - (RA / DEG / 15);
  // Normalize equation of time
  while (eqt > 12) eqt -= 24;
  while (eqt < -12) eqt += 24;
  return { declination: dec / DEG, equation: eqt };
}

function hourAngle(lat: number, dec: number, angle: number): number {
  const latR = lat * DEG;
  const decR = dec * DEG;
  const cosHA = (-Math.sin(angle * DEG) - Math.sin(latR) * Math.sin(decR)) /
    (Math.cos(latR) * Math.cos(decR));
  if (cosHA > 1) return 0; // sun never reaches this angle (high latitude)
  if (cosHA < -1) return 12; // midnight sun
  return Math.acos(cosHA) / DEG / 15;
}

function asrHourAngle(lat: number, dec: number): number {
  // Shafi'i: shadow = 1x object length + noon shadow
  const noonZenith = Math.abs(lat - dec);
  const asrAlt = Math.atan(1 / (1 + Math.tan(noonZenith * DEG))) / DEG;
  // hourAngle expects depression angle; Asr altitude is above horizon, so negate
  return hourAngle(lat, dec, -asrAlt);
}

function horizonDip(altitudeMeters: number): number {
  if (altitudeMeters <= 0) return 0;
  return Math.acos(EARTH_R / (EARTH_R + altitudeMeters)) / DEG;
}

export function calculatePrayerTimes(
  lat: number,
  lng: number,
  date: Date,
  altitudeMeters: number = 0,
): PrayerTimes {
  const year = date.getUTCFullYear();
  const month = date.getUTCMonth() + 1;
  const day = date.getUTCDate();
  const jd = julianDate(year, month, day);
  const sun = sunPosition(jd);
  const dip = horizonDip(altitudeMeters);

  // Transit (Dhuhr) in UTC hours
  const transit = 12 - sun.equation - lng / 15;

  // Sunrise/sunset angle adjusted for altitude
  const sunriseAngle = 0.833 + dip;

  const sunriseHA = hourAngle(lat, sun.declination, sunriseAngle);
  const fajrHA = hourAngle(lat, sun.declination, FAJR_ANGLE + dip);
  const asrHA = asrHourAngle(lat, sun.declination);

  const fajrH = transit - fajrHA;
  const sunriseH = transit - sunriseHA;
  const dhuhrH = transit;
  const asrH = transit + asrHA;
  const maghribH = transit + sunriseHA;
  const ishaH = maghribH + ISHA_MINUTES / 60; // Umm Al-Qura

  function toDate(hours: number): Date {
    let h = hours;
    let d = day;
    while (h < 0) { h += 24; d -= 1; }
    while (h >= 24) { h -= 24; d += 1; }
    const hh = Math.floor(h);
    const mm = Math.round((h - hh) * 60);
    const result = new Date(Date.UTC(year, month - 1, d, hh, mm));
    return result;
  }

  return {
    fajr: toDate(fajrH),
    sunrise: toDate(sunriseH),
    dhuhr: toDate(dhuhrH),
    asr: toDate(asrH),
    maghrib: toDate(maghribH),
    isha: toDate(ishaH),
  };
}

export function parseCoordinate(raw: string): number {
  // Format: N0244.6 or E10141.9 or S0130.0 or W00530.5
  const sign = raw[0] === "S" || raw[0] === "W" ? -1 : 1;
  const nums = raw.slice(1);
  const dotIdx = nums.indexOf(".");
  const minPart = nums.slice(dotIdx - 2); // last 2 digits before dot + decimal
  const degPart = nums.slice(0, dotIdx - 2);
  const deg = parseInt(degPart, 10);
  const min = parseFloat(minPart);
  return sign * (deg + min / 60);
}

export function flToMeters(fl: string | null): number {
  if (!fl) return 0;
  const num = parseInt(fl.replace("FL", ""), 10);
  if (isNaN(num)) return 0;
  return num * 100 * 0.3048; // FL × 100 feet → meters
}
