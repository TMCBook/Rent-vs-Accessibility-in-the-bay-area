"""Build per-ZIP data for the Bay Area affordability + access map.

Inputs (What is used): Zillow parts 1-3, Google Maps Places, Google Maps, Reviews, Indeed job listings. 
ZIP shapes: Census 2010 ZCTAs (OpenDataDE GeoJSON).
Output: ../data/zips.json (geometry + metrics), ../data/summary.json
"""
import json, re, math, os
import duckdb, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import shape, mapping, Point
from shapely import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
# Raw dataset folders (zillow/, places/, reviews/, indeed/) and the Census ZIP GeoJSON:
D = os.environ.get("DATA_DIR", os.path.join(HERE, "..", "raw"))
ZIP_GEOJSON = os.environ.get("ZIP_GEOJSON", os.path.join(D, "ca_california_zip_codes_geo.min.json"))
OUT = os.path.join(HERE, "..", "data")
con = duckdb.connect(); con.sql("SET threads=8")
RC = "max_line_size=50000000, ignore_errors=true, sample_size=-1"
BAY = ["Alameda", "Contra Costa", "Marin", "Napa", "San Francisco", "San Mateo",
       "Santa Clara", "Solano", "Sonoma"]

# ---------- Zillow ----------
z = con.sql(f"""
  select zpid, homeStatus, try_cast(price as double) price, try_cast(bedrooms as double) beds,
         try_cast(zipcode as int) zip, city, county, try_cast(latitude as double) lat,
         try_cast(longitude as double) lon, try_cast(rentZestimate as double) rentz,
         getting_around_scores gas
  from read_csv('{D}/zillow/zillow_part*.csv', union_by_name=true, {RC})
""").df()
z = z.drop_duplicates("zpid")
z["county"] = z["county"].str.replace(" County", "", regex=False)
z = z[z.county.isin(BAY) & z.lat.notna() & z.zip.notna()]
z["zip"] = z.zip.astype(int).astype(str).str.zfill(5)

def score(s, key):
    if not isinstance(s, str): return np.nan
    m = re.search(r'"%s":"(\d+)/100' % key, s)
    return float(m.group(1)) if m else np.nan
z["walk"] = z.gas.map(lambda s: score(s, "walk_score"))
z["transit"] = z.gas.map(lambda s: score(s, "transit_score"))

rent = z[(z.homeStatus == "FOR_RENT") & z.price.between(500, 20000)].copy()
sold = z[(z.homeStatus == "RECENTLY_SOLD") & z.price.between(50_000, 50_000_000)]
print("rentals", len(rent), "sold", len(sold))

# ---------- Places ----------
p = con.sql(f"""select place_id, name, category, try_cast(rating as double) rating,
  try_cast(reviews_count as double) nrev, try_cast(lat as double) lat, try_cast(lon as double) lon,
  permanently_closed from read_csv('{D}/places/google_maps.csv', {RC})""").df()
p = p[p.lat.notna() & (p.permanently_closed.astype(str).str.lower() != "true")]
p.loc[(p.rating <= 0) | ~(p.nrev > 0), "rating"] = np.nan  # 0 = no reviews yet
GROUPS = {
  "grocery": ["Grocery store", "Supermarket", "Asian grocery store", "Mexican grocery store",
              "Produce market", "Health food store", "Discount supermarket"],
  "clinic": ["Medical clinic", "Family practice physician", "Internist", "Pediatrician",
             "Medical Center", "Hospital", "Emergency care physician", "Community health centre",
             "Community health center", "General practitioner", "Urgent care center",
             "Walk-in clinic", "Emergency room"],
  "pharmacy": ["Pharmacy", "Drug store"],
  "transit": ["Bus stop", "Transit station", "Train station", "Subway station",
              "Light rail station", "Bus station"],
  "foodbank": ["Food bank", "Food pantry", "Soup kitchen"],
  "childcare": ["Day care center", "Preschool", "Child care agency", "Family day care service"],
  "bank": ["Bank", "Credit union"],
  "checkcash": ["Check cashing service", "Money transfer service"],
}
cat2g = {c: g for g, cs in GROUPS.items() for c in cs}
p["group"] = p.category.map(cat2g)
print(p.group.value_counts())

# equirectangular projection in km, fine at this scale
LAT0 = math.radians(37.75)
def xy(lat, lon): return np.c_[np.asarray(lon) * 111.32 * math.cos(LAT0), np.asarray(lat) * 110.57]
MI = 1.60934
rxy = xy(rent.lat, rent.lon)
for g in ["grocery", "clinic", "pharmacy", "transit", "foodbank"]:
    pts = p[p.group == g]
    d, _ = cKDTree(xy(pts.lat, pts.lon)).query(rxy)
    rent["d_" + g] = d / MI  # miles
rent["all_ess"] = ((rent.d_grocery <= 1) & (rent.d_clinic <= 1) & (rent.d_pharmacy <= 1)
                   & (rent.d_transit <= 0.25))

# ---------- ZIP shapes ----------
gj = json.load(open(ZIP_GEOJSON))
zip_meta = (z.groupby("zip").agg(city=("city", lambda s: s.mode().iat[0]),
                                 county=("county", lambda s: s.mode().iat[0]),
                                 n_all=("zpid", "size")))
zip_meta = zip_meta[zip_meta.n_all >= 5]
feats = {f["properties"]["ZCTA5CE10"]: f for f in gj["features"]
         if f["properties"]["ZCTA5CE10"] in zip_meta.index}
geoms = {k: shape(f["geometry"]) for k, f in feats.items()}
keys = list(geoms); tree = STRtree([geoms[k] for k in keys])
def zip_of(lat, lon):
    pt = Point(lon, lat)
    for i in tree.query(pt, predicate="intersects"): return keys[i]
    return None
p["zip"] = [zip_of(a, b) for a, b in zip(p.lat, p.lon)]
p = p[p.zip.notna()]

# ---------- Reviews (essential services only) ----------
ess_ids = p[p.group.isin(["grocery", "clinic", "pharmacy", "foodbank"])][["place_id", "zip", "group"]]
r = con.sql(f"""select place_id, try_cast(review_rating as double) stars,
   response_of_owner is not null and length(trim(response_of_owner))>0 replied
   from read_csv('{D}/reviews/google_maps_reviews.csv', {RC})""").df()
r = r.merge(ess_ids, on="place_id")
print("essential reviews matched", len(r))

# ---------- Indeed ----------
j = con.sql(f"""select job_title, company_name, location, salary_formatted sal, job_type
   from read_csv('{D}/indeed/indeed_job_listings.csv', {RC})""").df()
j = j.drop_duplicates(["job_title", "company_name", "location"])
num = r"\$?([\d,]+(?:\.\d+)?)\s*([kK])?"
def parse(s):
    if not isinstance(s, str): return (np.nan, None)
    t = s.lower()
    vals = [float(a.replace(",", "")) * (1000 if k else 1) for a, k in re.findall(num, s) if a.replace(",", "").replace(".", "")]
    if not vals: return (np.nan, None)
    v = sum(vals[:2]) / len(vals[:2])
    if "hour" in t or "hora" in t: return (v, "hour")
    if "year" in t or "año" in t or "ano" in t: return (v / 2080, "year")
    if "month" in t or "mes" in t: return (v * 12 / 2080, "month")
    if "week" in t or "semana" in t: return (v / 40, "week")
    if "day" in t or "día" in t or "dia" in t: return (v / 8, "day")
    return (np.nan, None)
pr = j.sal.map(parse)
j["hourly"] = [a for a, _ in pr]; j["unit"] = [b for _, b in pr]
j.loc[~j.hourly.between(10, 500), "hourly"] = np.nan
loc = j.location.fillna("").str.extract(r"(?:^|,\s*)([A-Za-z][A-Za-z .'\-]+),\s*CA(?:\s+(\d{5}))?\s*$")
j["jcity"] = loc[0].str.strip(); j["jzip"] = loc[1]
bay_cities = set(z.city.dropna().unique())
j = j[j.jcity.isin(bay_cities) | j.jzip.isin(zip_meta.index)]
print("bay postings", len(j), "with pay", j.sal.notna().mean())
hourly_jobs = j[j.unit == "hour"]
REGION_WAGE = float(hourly_jobs.hourly.median())
print("region median hourly (hourly-paid postings)", REGION_WAGE)
city_jobs = j.groupby("jcity").agg(jobs=("job_title", "size"), pay_share=("sal", lambda s: s.notna().mean()))
city_wage = hourly_jobs.groupby("jcity").hourly.agg(["median", "size"])

# ---------- Aggregate per ZIP ----------
def r1(x, n=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), n)
rows = {}
for zp, m in zip_meta.iterrows():
    if zp not in geoms: continue
    rr = rent[rent.zip == zp]; ss = sold[sold.zip == zp]; zz = z[z.zip == zp]
    pp = p[p.zip == zp]; rv = r[r.zip == zp]
    cnt = pp.group.value_counts().to_dict()
    ess = pp[pp.group.isin(["grocery", "clinic", "pharmacy"])]
    cw = city_wage.loc[m.city] if m.city in city_wage.index else None
    wage = float(cw["median"]) if cw is not None and cw["size"] >= 20 else REGION_WAGE
    med_rent = float(rr.price.median()) if len(rr) >= 8 else None
    one_br = rr[rr.beds == 1].price
    cj = city_jobs.loc[m.city] if m.city in city_jobs.index else None
    rows[zp] = dict(
        zip=zp, city=m.city, county=m.county,
        n_rent=int(len(rr)), rent=r1(med_rent, 0),
        rent_1br=r1(one_br.median(), 0) if len(one_br) >= 5 else None,
        rent_zest=r1(zz.rentz.median(), 0),
        sold=r1(ss.price.median(), -3) if len(ss) >= 5 else None, n_sold=int(len(ss)),
        walk=r1(zz.walk.median(), 0), transit=r1(zz.transit.median(), 0),
        d_grocery=r1(rr.d_grocery.median(), 2), d_clinic=r1(rr.d_clinic.median(), 2),
        d_pharmacy=r1(rr.d_pharmacy.median(), 2), d_foodbank=r1(rr.d_foodbank.median(), 2),
        bus_quarter=r1((rr.d_transit <= 0.25).mean() * 100, 0) if len(rr) else None,
        all_ess=r1(rr.all_ess.mean() * 100, 0) if len(rr) >= 8 else None,
        counts={g: int(cnt.get(g, 0)) for g in GROUPS},
        ess_rating=r1(ess.rating.mean(), 2) if ess.rating.notna().sum() >= 3 else None,
        n_ess_rated=int(ess.rating.notna().sum()),
        rev_n=int(len(rv)), rev_stars=r1(rv.stars.mean(), 2) if len(rv) >= 10 else None,
        rev_reply=r1(rv.replied.mean() * 100, 0) if len(rv) >= 10 else None,
        wage=r1(wage, 2), wage_local=bool(cw is not None and cw["size"] >= 20),
        city_jobs=int(cj["jobs"]) if cj is not None else 0,
        city_pay_share=r1(cj["pay_share"] * 100, 0) if cj is not None else None,
        burden=r1(med_rent / (wage * 2080 / 12) * 100, 0) if med_rent else None,
        hours=r1(med_rent / wage, 0) if med_rent else None,
    )

df = pd.DataFrame(rows.values())
valid = df[df.rent.notna() & df.all_ess.notna()]
rent_med = valid.rent.median(); acc_med = valid.all_ess.median()
for zp, row in rows.items():
    if row["rent"] is None or row["all_ess"] is None: row["group"] = "nodata"; continue
    cheap = row["rent"] <= rent_med; good = row["all_ess"] >= acc_med
    row["group"] = {(True, True): "both", (True, False): "underserved",
                    (False, True): "priced_out", (False, False): "neither"}[(cheap, good)]
    # percentile ranks for the panel
    row["rent_pct"] = round(float((valid.rent < row["rent"]).mean() * 100))
    row["acc_pct"] = round(float((valid.all_ess < row["all_ess"]).mean() * 100))

# ---------- Geometry out (simplified, rounded) ----------
def rnd(o):
    if isinstance(o, (list, tuple)):
        if o and isinstance(o[0], (int, float)): return [round(o[0], 4), round(o[1], 4)]
        return [rnd(x) for x in o]
    return o
features = []
for zp, row in rows.items():
    g = geoms[zp].simplify(0.0006, preserve_topology=True)
    gm = mapping(g)
    features.append({"type": "Feature", "id": zp,
                     "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])},
                     "properties": row})
json.dump({"type": "FeatureCollection", "features": features}, open(f"{OUT}/zips.json", "w"),
          separators=(",", ":"))

summary = dict(
    n_zips=len(rows), n_rentals=int(len(rent)), n_places=int(p.group.notna().sum()),
    n_postings=int(len(j)), pay_share=r1(j.sal.notna().mean() * 100, 0),
    region_wage=r1(REGION_WAGE, 2), rent_median=r1(rent.price.median(), 0),
    zip_rent_median=r1(rent_med, 0), zip_access_median=r1(acc_med, 0),
    region_all_ess=r1(rent.all_ess.mean() * 100, 0),
    burden_region=r1(rent.price.median() / (REGION_WAGE * 2080 / 12) * 100, 0),
    share_rent_affordable=r1((rent.price <= REGION_WAGE * 2080 / 12 * 0.3).mean() * 100, 1),
    affordable_listings=int((rent.price <= REGION_WAGE * 2080 / 12 * 0.3).sum()),
    affordable_with_access=r1(rent[rent.price <= REGION_WAGE * 2080 / 12 * 0.3].all_ess.mean() * 100, 0),
    groups=df.assign(group=[rows[k]["group"] for k in df.zip]).group.value_counts().to_dict(),
)
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
