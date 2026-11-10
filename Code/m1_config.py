"""Model 1 configuration: representative section, data sources, fixed constants.

Everything that is a *choice* of the team (section, windows, thresholds) lives here
so that it is stated once, can be cited in the paper, and can be changed in one place.
Nothing in this file is "given by the problem statement" except the scale ranges
quoted in SECTION["problem_scale"].
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "Data" / "raw" / "model1"            # original API responses (gz) + manifest
PROC = ROOT / "Data" / "processed" / "model1"      # derived tables used by the model
RES = ROOT / "Results" / "model1"                  # numbers reported in the paper
FIG = ROOT / "Figures" / "model1"                  # diagnostic figures (matplotlib)

# ---------------------------------------------------------------------------
# 1. Representative section (ASSUMPTION A1 -- team choice, not given by the problem)
# ---------------------------------------------------------------------------
# Southern margin of the Taklamakan between the Yutian (Keriya) and Minfeng (Niya)
# oases.  Reasons: (i) the belt was closed here in Nov 2024 (last gap, Yutian);
# (ii) two documented 2024 projects lie in it (Data/raw/local_project_evidence:
# Minfeng 8,667 ha biological + Yutian 7,000 ha engineering sand fixation);
# (iii) the Tarim Desert Highway shelterbelt, whose irrigation regime is published,
# ends at Minfeng, so literature parameters are transferable.
# The belt has no public GIS boundary.  We therefore model a *stylised* strip and
# say so; length/width only fix the area used to scale per-hectare results.
SECTION = {
    "name": "Yutian-Minfeng southern-margin section",
    "length_km": 100.0,        # along the margin (problem: tens to hundreds of km)
    "width_km": 1.5,           # across the margin (problem: tens of m to several km)
    "area_ha": 15000.0,        # 100 km x 1.5 km; same magnitude as 15,667 ha planned (G02)
    "problem_scale": "tens of m - several km wide; tens - hundreds of km long (Task 1)",
}

# MODIS area used to *locate* the oasis-desert fringe objectively (sinusoidal box).
AREA = {"lat": 37.05, "lon": 82.15, "km_ns": 40, "km_ew": 85}
EPOCH_EARLY = (2001, 2002, 2003)      # "before" state
EPOCH_LATE = (2022, 2023, 2024)       # "after" state
SUMMER_DOYS = (209, 225)              # late Jul / mid Aug 16-day composites (peak green)

# Pixel classes from mean summer NDVI in the two epochs (E = early, L = late).
# Thresholds are operational definitions (ASSUMPTION A2); the bare-sand level
# (~0.06) and dense-oasis level (>0.4) are read from the data, see m1_build_dataset.
CLASS_RULES = {
    "desert":    "E < 0.08 and L < 0.08          (bare reference, soil end-member)",
    "ecotone":   "0.09 <= E <= 0.20 and |L-E| < 0.04   (natural sparse vegetation, no conversion)",
    "converted": "E < 0.10 and L >= 0.25         (bare in 2001-03, vegetated by 2022-24: treated/irrigated)",
    "oasis":     "E >= 0.40 and L >= 0.40        (dense vegetation, vegetation end-member)",
}
WINDOWS_PER_CLASS = {"converted": 4, "ecotone": 3, "desert": 2, "oasis": 2}
WINDOW_KM = 1                # ORNL kmAboveBelow = kmLeftRight = 1  -> 9 x 9 pixels of 231.66 m
MIN_SEPARATION_KM = 6.0      # between windows of the same class

# ---------------------------------------------------------------------------
# 2. Data sources (all public, no account).  Period chosen to cover the whole
#    MOD13Q1 record so that establishment of vegetation (not only 2015-24) is seen.
# ---------------------------------------------------------------------------
Y0, Y1 = 2001, 2024
MODIS_PRODUCT = "MOD13Q1"            # v061, 250 m, 16-day; via ORNL DAAC subset API
MODIS_API = "https://modis.ornl.gov/rst/api/v1"
MODIS_BANDS = ("250m_16_days_NDVI", "250m_16_days_pixel_reliability")
SIN_R = 6371007.181                  # MODIS sinusoidal sphere radius (m)

OPENMETEO_API = "https://archive-api.open-meteo.com/v1/archive"
# 'era5_seamless' is requested EXPLICITLY.  It returns ERA5-Land (0.1 deg) for
# temperature / dew point / soil layers and ERA5 (0.25 deg) for wind, gusts,
# precipitation, radiation and pressure.  The legacy panel used the default
# 'best_match', which silently mixes models and changes over time.
OPENMETEO_MODEL = "era5_seamless"
OPENMETEO_TZ = "Asia/Urumqi"         # UTC+6, close to local solar time at 82 E
OM_DAILY = ("temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
            "dew_point_2m_mean,precipitation_sum,shortwave_radiation_sum,"
            "wind_speed_10m_mean,surface_pressure_mean,et0_fao_evapotranspiration,"
            "soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean,"
            "soil_moisture_28_to_100cm_mean")
OM_HOURLY = "wind_speed_10m,wind_gusts_10m,wind_direction_10m"

# Forcing sites: three points along the section (west / middle / east).  Each MODIS
# window uses the nearest one.  Coordinates are requests; the API returns its grid.
FORCING_SITES = {
    "W_yutian": (36.95, 81.95),
    "M_gap":    (37.00, 82.35),
    "E_minfeng": (37.10, 82.75),
}

POWER_API = "https://power.larc.nasa.gov/api/temporal/daily/point"   # independent cross-check
POWER_PARAMS = "T2M_MAX,T2M_MIN,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR,PS"

USER_AGENT = "desertification-control-practice/1.0 (student modelling exercise)"
