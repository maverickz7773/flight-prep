from __future__ import annotations
from pydantic import BaseModel


class FlightInfo(BaseModel):
    flight_number: str
    callsign: str | None = None
    date: str
    departure_icao: str
    arrival_icao: str
    aircraft_type: str
    registration: str
    etops_minutes: int | None = None
    cost_index: int | None = None
    std: str
    sta: str
    block_time: str
    trip_time: str
    departure_utc_offset: str | None = None
    arrival_utc_offset: str | None = None
    dispatcher: str | None = None
    pic: str | None = None
    cruise_levels: list[str] = []
    departure_runway: str | None = None
    arrival_runway: str | None = None
    sid: str | None = None
    star: str | None = None
    route_string: str | None = None
    ground_distance: int | None = None
    wind_component: str | None = None


class FuelSummary(BaseModel):
    taxi: int
    taxi_time: str | None = None
    trip: int
    trip_time: str | None = None
    contingency: int
    contingency_type: str | None = None
    contingency_time: str | None = None
    alternate: int
    alternate_airport: str | None = None
    alternate_time: str | None = None
    final_reserve: int
    final_reserve_time: str | None = None
    extra: int
    extra_time: str | None = None
    ramp: int
    ramp_time: str | None = None
    takeoff: int | None = None
    min_fuel_required: int | None = None
    min_fuel_time: str | None = None
    expected_landing: int | None = None
    plan_req: float | None = None
    plan_rem: float | None = None
    plan_margin: float | None = None


class Weights(BaseModel):
    mzfw: int
    ezfw: int
    mtow: int
    etow: int
    mlwt: int
    elwt: int
    ezfw_pct: float | None = None
    etow_pct: float | None = None
    elwt_pct: float | None = None


class TakeoffData(BaseModel):
    runway: str | None = None
    sid: str | None = None
    v1: str | None = None
    vr: str | None = None
    v2: str | None = None
    flaps: str | None = None
    toc_temperature: str | None = None
    wind_at_departure: str | None = None
    remarks: str | None = None


class Waypoint(BaseModel):
    name: str
    airway: str | None = None
    flight_level: str | None = None
    true_track: int | None = None
    wind: str | None = None
    ground_speed: int | None = None
    tas: int | None = None
    fuel_remaining: float | None = None
    shear_rate: int | None = None
    eta: str | None = None
    distance: int | None = None
    is_toc: bool = False
    is_tod: bool = False
    is_step_climb: bool = False
    fir_name: str | None = None
    fir_icao: str | None = None
    latitude: str | None = None
    longitude: str | None = None


class ETOPSPoint(BaseModel):
    point_type: str
    eet: str | None = None
    position: str | None = None
    alternate_icao: str | None = None
    alternate_icao_2: str | None = None
    fuel_remaining: float | None = None


class ETOPSAlternate(BaseModel):
    icao: str
    runway: str | None = None
    period: str | None = None
    approach: str | None = None
    weather: str | None = None
    minima: str | None = None


class ETOPSSector(BaseModel):
    sector_number: int
    entry_icao: str | None = None
    entry_eet: str | None = None
    entry_fuel: float | None = None
    exit_icao: str | None = None
    exit_eet: str | None = None
    exit_fuel: float | None = None
    alternates: list[str] = []


class ETOPSInfo(BaseModel):
    sectors: list["ETOPSSector"] = []
    entry: ETOPSPoint | None = None
    exit: ETOPSPoint | None = None
    etp_points: list[ETOPSPoint] = []
    suitable_alternates: list[ETOPSAlternate] = []


class RouteSummary(BaseModel):
    route_string: str
    waypoints: list[Waypoint] = []
    fir_sequence: list[str] = []
    enroute_info: list["EnrouteInfoItem"] = []
    highest_mora: str | None = None
    cruise_flight_levels: list[str] = []


class EnrouteInfoItem(BaseModel):
    fir_icao: str
    fir_name: str
    notes: str


class NATSOverview(BaseModel):
    tmi: str | None = None
    route: str | None = None
    entry_point: str | None = None
    entry_eet: str | None = None
    entry_fir: str | None = None
    exit_point: str | None = None
    exit_eet: str | None = None
    exit_fir: str | None = None


class NATSProcedure(BaseModel):
    trigger_firs: list[str] = []
    overview_text: str
    preflight_text: str
    enroute_text: str
    exit_text: str
    enroute_fir_callouts: list[str] = []
    overview: NATSOverview


class AlternateInfo(BaseModel):
    icao: str
    runway: str | None = None
    distance: int | None = None
    flight_level: str | None = None
    wind_component: str | None = None
    time: str | None = None
    fuel: int | None = None
    route: str | None = None


class ArrivalInfo(BaseModel):
    runway: str | None = None
    star: str | None = None
    alternates: list[AlternateInfo] = []


class AirportWeather(BaseModel):
    icao: str
    name: str | None = None
    metar: str | None = None
    taf: str | None = None


class SIGMET(BaseModel):
    fir_icao: str
    fir_name: str | None = None
    raw_text: str
    phenomenon: str | None = None
    top: str | None = None


class FIRWeatherBlock(BaseModel):
    fir_icao: str
    fir_name: str
    sigmets: list[SIGMET] = []
    airports: list[AirportWeather] = []


class WeatherData(BaseModel):
    departure: AirportWeather | None = None
    destination: AirportWeather | None = None
    alternates: list[AirportWeather] = []
    enroute: list[FIRWeatherBlock] = []


class NOTAMItem(BaseModel):
    reference: str
    valid_from: str | None = None
    valid_to: str | None = None
    category: str
    subcategory: str | None = None
    text: str
    relevance: str = "MEDIUM"
    summary: str | None = None


class AirportNotamBlock(BaseModel):
    icao: str
    name: str | None = None
    notams: list[NOTAMItem] = []


class FIRNotamBlock(BaseModel):
    fir_icao: str
    fir_name: str
    notams: list[NOTAMItem] = []


class NOTAMData(BaseModel):
    departure: list[NOTAMItem] = []
    destination: list[NOTAMItem] = []
    alternates: list[AirportNotamBlock] = []
    enroute_airports: list[AirportNotamBlock] = []
    enroute: list[FIRNotamBlock] = []


class MELItem(BaseModel):
    reference: str
    description: str
    remark: str | None = None


class CrewAlert(BaseModel):
    reference: str | None = None
    subject: str
    text: str


class OperationalInsight(BaseModel):
    severity: str
    text: str


class AerodromeBriefing(BaseModel):
    icao: str
    name: str
    category: str
    general: str | None = None
    company_policy: str | None = None
    atc: str | None = None
    arrival_procedures: str | None = None
    ground_maneuvering: str | None = None
    departure_procedures: str | None = None
    miscellaneous: str | None = None
    destination_alternates: str | None = None


class AirportNotes(BaseModel):
    departure: str | None = None
    arrival: str | None = None


class AirportFeedbackEntry(BaseModel):
    id: int
    section: str
    airport_icao: str
    flight_date: str
    route_text: str | None = None
    from_icao: str
    to_icao: str
    sid: str | None = None
    star: str | None = None
    runway: str | None = None
    approach_runway: str | None = None
    comments: str
    created_at: str


class AirportFeedback(BaseModel):
    departure: list["AirportFeedbackEntry"] = []
    arrival: list["AirportFeedbackEntry"] = []


class AirportFeedbackCreate(BaseModel):
    section: str
    airport_icao: str
    flight_date: str
    route_text: str | None = None
    from_icao: str
    to_icao: str
    sid: str | None = None
    star: str | None = None
    runway: str | None = None
    approach_runway: str | None = None
    comments: str


class DeleteStatus(BaseModel):
    deleted: bool


class ParseJobStart(BaseModel):
    job_id: str
    status: str


class ParseJobStatus(BaseModel):
    job_id: str
    status: str
    result: BriefingData | None = None
    error: str | None = None


class BriefingData(BaseModel):
    flight_info: FlightInfo
    fuel: FuelSummary
    weights: Weights
    takeoff: TakeoffData
    route: RouteSummary
    etops: ETOPSInfo | None = None
    arrival: ArrivalInfo
    weather: WeatherData
    notams: NOTAMData
    mel_items: list[MELItem] = []
    crew_alerts: list[CrewAlert] = []
    operational_insights: list[OperationalInsight] = []
    enroute_airport_list: list[str] = []
    departure_briefing: AerodromeBriefing | None = None
    arrival_briefing: AerodromeBriefing | None = None
    airport_notes: AirportNotes | None = None
    airport_feedback: AirportFeedback | None = None
    nats_procedure: NATSProcedure | None = None
