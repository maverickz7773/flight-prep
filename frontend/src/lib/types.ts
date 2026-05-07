export interface FlightInfo {
  flight_number: string;
  callsign: string | null;
  date: string;
  departure_icao: string;
  arrival_icao: string;
  aircraft_type: string;
  registration: string;
  etops_minutes: number | null;
  cost_index: number | null;
  std: string;
  sta: string;
  block_time: string;
  trip_time: string;
  departure_utc_offset: string | null;
  arrival_utc_offset: string | null;
  dispatcher: string | null;
  pic: string | null;
  cruise_levels: string[];
  departure_runway: string | null;
  arrival_runway: string | null;
  sid: string | null;
  star: string | null;
  route_string: string | null;
  ground_distance: number | null;
  wind_component: string | null;
}

export interface FuelSummary {
  taxi: number;
  taxi_time: string | null;
  trip: number;
  trip_time: string | null;
  contingency: number;
  contingency_type: string | null;
  contingency_time: string | null;
  alternate: number;
  alternate_airport: string | null;
  alternate_time: string | null;
  final_reserve: number;
  final_reserve_time: string | null;
  extra: number;
  extra_time: string | null;
  ramp: number;
  ramp_time: string | null;
  takeoff: number | null;
  min_fuel_required: number | null;
  min_fuel_time: string | null;
  expected_landing: number | null;
  plan_req: number | null;
  plan_rem: number | null;
  plan_margin: number | null;
}

export interface Weights {
  mzfw: number;
  ezfw: number;
  mtow: number;
  etow: number;
  mlwt: number;
  elwt: number;
  ezfw_pct: number | null;
  etow_pct: number | null;
  elwt_pct: number | null;
}

export interface TakeoffData {
  runway: string | null;
  sid: string | null;
  v1: string | null;
  vr: string | null;
  v2: string | null;
  flaps: string | null;
  toc_temperature: string | null;
  wind_at_departure: string | null;
  remarks: string | null;
}

export interface Waypoint {
  name: string;
  airway: string | null;
  flight_level: string | null;
  true_track: number | null;
  ground_speed: number | null;
  tas: number | null;
  eta: string | null;
  fuel_remaining: number | null;
  shear_rate: number | null;
  is_toc: boolean;
  is_tod: boolean;
  is_step_climb: boolean;
  fir_name: string | null;
  fir_icao: string | null;
  latitude: string | null;
  longitude: string | null;
}

export interface ETOPSPoint {
  point_type: string;
  eet: string | null;
  position: string | null;
  alternate_icao: string | null;
  alternate_icao_2: string | null;
  fuel_remaining: number | null;
}

export interface ETOPSAlternate {
  icao: string;
  runway: string | null;
  period: string | null;
  approach: string | null;
  weather: string | null;
  minima: string | null;
}

export interface ETOPSInfo {
  entry: ETOPSPoint | null;
  exit: ETOPSPoint | null;
  etp_points: ETOPSPoint[];
  suitable_alternates: ETOPSAlternate[];
}

export interface RouteSummary {
  route_string: string;
  waypoints: Waypoint[];
  fir_sequence: string[];
  highest_mora: string | null;
  cruise_flight_levels: string[];
}

export interface AlternateInfo {
  icao: string;
  runway: string | null;
  distance: number | null;
  flight_level: string | null;
  wind_component: string | null;
  time: string | null;
  fuel: number | null;
  route: string | null;
}

export interface ArrivalInfo {
  runway: string | null;
  star: string | null;
  alternates: AlternateInfo[];
}

export interface AirportWeather {
  icao: string;
  name: string | null;
  metar: string | null;
  taf: string | null;
}

export interface SIGMET {
  fir_icao: string;
  fir_name: string | null;
  raw_text: string;
  phenomenon: string | null;
  top: string | null;
}

export interface FIRWeatherBlock {
  fir_icao: string;
  fir_name: string;
  sigmets: SIGMET[];
  airports: AirportWeather[];
}

export interface WeatherData {
  departure: AirportWeather | null;
  destination: AirportWeather | null;
  alternates: AirportWeather[];
  enroute: FIRWeatherBlock[];
}

export interface NOTAMItem {
  reference: string;
  valid_from: string | null;
  valid_to: string | null;
  category: string;
  subcategory: string | null;
  text: string;
  relevance: string;
  summary: string | null;
}

export interface AirportNotamBlock {
  icao: string;
  name: string | null;
  notams: NOTAMItem[];
}

export interface FIRNotamBlock {
  fir_icao: string;
  fir_name: string;
  notams: NOTAMItem[];
}

export interface NOTAMData {
  departure: NOTAMItem[];
  destination: NOTAMItem[];
  alternates: AirportNotamBlock[];
  enroute_airports: AirportNotamBlock[];
  enroute: FIRNotamBlock[];
}

export interface MELItem {
  reference: string;
  description: string;
  remark: string | null;
}

export interface CrewAlert {
  reference: string | null;
  subject: string;
  text: string;
}

export interface OperationalInsight {
  severity: string;
  text: string;
}

export interface AerodromeBriefing {
  icao: string;
  name: string;
  category: string;
  general: string | null;
  company_policy: string | null;
  atc: string | null;
  arrival_procedures: string | null;
  ground_maneuvering: string | null;
  departure_procedures: string | null;
  miscellaneous: string | null;
  destination_alternates: string | null;
}

export interface AirportNotes {
  departure: string | null;
  arrival: string | null;
}

export interface ParseJobStart {
  job_id: string;
  status: string;
}

export interface ParseJobStatus {
  job_id: string;
  status: string;
  result: BriefingData | null;
  error: string | null;
}

export interface BriefingData {
  flight_info: FlightInfo;
  fuel: FuelSummary;
  weights: Weights;
  takeoff: TakeoffData;
  route: RouteSummary;
  etops: ETOPSInfo | null;
  arrival: ArrivalInfo;
  weather: WeatherData;
  notams: NOTAMData;
  mel_items: MELItem[];
  crew_alerts: CrewAlert[];
  operational_insights: OperationalInsight[];
  enroute_airport_list: string[];
  departure_briefing: AerodromeBriefing | null;
  arrival_briefing: AerodromeBriefing | null;
  airport_notes: AirportNotes | null;
}
