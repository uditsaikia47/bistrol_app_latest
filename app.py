import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import Fullscreen, MiniMap, LocateControl
from streamlit_folium import st_folium
from geopy.distance import geodesic
import base64
import os
import json
import pandas as pd

st.set_page_config(layout="wide", page_title="Field Survey Navigator", page_icon="🗺️")

BASE         = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH    = os.path.join(BASE, "idEMAs66s4_1773329559498.png")
PROGRESS_FILE = os.path.join(BASE, "survey_progress.json")

logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
logo_html = (f'<img src="data:image/png;base64,{logo_b64}" style="height:36px;object-fit:contain">') if logo_b64 else ""

MAP_H = 700

# ── CSS ─────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
*,*::before,*::after{font-family:'Inter',sans-serif;box-sizing:border-box;margin:0;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;overflow:hidden!important;}
html,body,[data-testid="stAppViewContainer"]{overflow:hidden!important;height:100vh!important;background:#0d1117!important;}
.topbar{position:fixed;top:0;left:0;right:0;height:62px;z-index:9999;
  background:#161b22;border-bottom:1px solid #30363d;
  padding:0 24px;display:flex;align-items:center;justify-content:space-between;}
.topbar-title{font-size:15px;font-weight:700;color:#f0f6fc;letter-spacing:2px;text-transform:uppercase;}
.topbar-sub{font-size:11px;color:#58a6ff;margin-top:2px;}
section[data-testid="stSidebar"]{background:#161b22!important;border-right:1px solid #30363d!important;
  top:62px!important;height:calc(100vh - 62px)!important;
  overflow-y:auto!important;overflow-x:hidden!important;padding-top:0!important;
  min-width:260px!important;max-width:260px!important;}
button[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"]{display:none!important;}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div{color:#c9d1d9!important;}
section[data-testid="stSidebar"] .stTextInput input{
  background:#0d1117!important;color:#f0f6fc!important;
  border:1px solid #30363d!important;border-radius:6px;font-size:12px!important;}
[data-testid="stAppViewContainer"]>section.main{
  margin-top:62px!important;height:calc(100vh - 62px)!important;overflow:hidden!important;background:#0d1117!important;}
div[data-testid="stHorizontalBlock"]{gap:0!important;align-items:flex-start!important;
  flex-wrap:nowrap!important;height:700px!important;overflow:hidden!important;}
div[data-testid="column"]:first-child{height:700px!important;overflow:hidden!important;
  padding:0!important;flex-shrink:0!important;}
div[data-testid="column"]:last-child{height:700px!important;max-height:700px!important;
  overflow:hidden!important;padding:0!important;
  background:#161b22!important;border-left:1px solid #30363d!important;flex-shrink:0!important;}
div[data-testid="column"]:last-child>div[data-testid="stVerticalBlock"]{
  height:700px!important;max-height:700px!important;
  overflow-y:scroll!important;overflow-x:hidden!important;
  padding:16px 20px 24px 22px!important;
  scrollbar-width:thin!important;scrollbar-color:#30363d #0d1117!important;}
div[data-testid="column"]:last-child>div[data-testid="stVerticalBlock"]::-webkit-scrollbar{width:4px;}
div[data-testid="column"]:last-child>div[data-testid="stVerticalBlock"]::-webkit-scrollbar-track{background:#0d1117;}
div[data-testid="column"]:last-child>div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px;}
div[data-testid="column"]:last-child>div[data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb:hover{background:#58a6ff;}
.sec-hdr{font-size:9px;font-weight:700;color:#8b949e;text-transform:uppercase;
  letter-spacing:2.5px;border-bottom:1px solid #21262d;padding-bottom:5px;margin:16px 0 8px 0;}
.sec-hdr:first-child{margin-top:0;}
.stProgress>div>div>div{background-color:#58a6ff!important;}
.stProgress>div>div{background:#21262d!important;border-radius:3px!important;height:3px!important;}
.metric-row{display:flex;gap:6px;margin:8px 0 4px 0;}
.metric-box{flex:1;min-width:0;background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:10px 4px 8px 4px;text-align:center;}
.metric-box .val{font-size:22px;font-weight:700;color:#58a6ff;line-height:1;}
.metric-box .val.green{color:#3fb950;}
.metric-box .val.orange{color:#d29922;}
.metric-box .lbl{font-size:9px;color:#8b949e;text-transform:uppercase;letter-spacing:1.5px;margin-top:4px;}
.sel-card{background:#0d1117;border:1px solid #21262d;border-left:3px solid #58a6ff;
  border-radius:8px;padding:10px 12px;margin-bottom:6px;}
.sel-card .sc-name{font-size:13px;font-weight:700;color:#58a6ff;margin-bottom:4px;line-height:1.3;}
.sel-card .sc-row{font-size:11px;color:#8b949e;line-height:1.9;}
.sel-card .sc-row b{color:#c9d1d9;}
.jump-hdr{font-size:9px;font-weight:700;color:#8b949e;text-transform:uppercase;
  letter-spacing:2.5px;border-bottom:1px solid #21262d;padding-bottom:5px;margin:16px 0 8px 0;}
div[data-testid="column"]:last-child .stSelectbox div[data-baseweb="select"]>div{
  background:#0d1117!important;border:1px solid #30363d!important;
  color:#f0f6fc!important;font-size:12px!important;font-weight:600!important;border-radius:6px!important;}
div[data-testid="column"]:last-child .stButton>button{
  background:#21262d!important;color:#c9d1d9!important;border:1px solid #30363d!important;
  border-radius:6px!important;font-size:11px!important;font-weight:600!important;
  padding:6px 4px!important;width:100%!important;transition:all .15s;}
div[data-testid="column"]:last-child .stButton>button:hover{border-color:#58a6ff!important;color:#58a6ff!important;background:#161b22!important;}
div[data-testid="column"]:last-child div[data-testid="stVerticalBlockBorderWrapper"]>div{
  background:#0d1117!important;border:1px solid #21262d!important;border-radius:6px!important;padding:4px 8px!important;}
div[data-testid="column"]:last-child .stTextArea textarea{
  background:#0d1117!important;color:#c9d1d9!important;border:1px solid #30363d!important;
  border-radius:6px!important;font-size:11px!important;resize:none!important;}
div[data-testid="column"]:last-child .stTextArea textarea:focus{border-color:#58a6ff!important;}
div[data-testid="column"]:last-child .stExpander{border:1px solid #21262d!important;border-radius:6px!important;background:#0d1117!important;}
div[data-testid="column"]:last-child .stExpander summary{font-size:10px!important;color:#8b949e!important;padding:4px 8px!important;}
div[data-testid="column"]:last-child .stRadio>div{gap:4px!important;}
div[data-testid="column"]:last-child .stRadio label{font-size:10px!important;color:#8b949e!important;padding:2px 6px!important;}
div[data-testid="column"]:last-child .stDownloadButton>button{
  background:#21262d!important;color:#58a6ff!important;border:1px solid #30363d!important;
  border-radius:6px!important;font-size:11px!important;font-weight:600!important;
  padding:6px 4px!important;width:100%!important;transition:all .15s;}
div[data-testid="column"]:last-child .stDownloadButton>button:hover{border-color:#58a6ff!important;background:#161b22!important;}
.sb-hdr{font-size:9px;font-weight:700;color:#8b949e;text-transform:uppercase;
  letter-spacing:2.5px;border-bottom:1px solid #21262d;padding-bottom:5px;margin:16px 0 8px 0;}
.s-item{font-size:11px;padding:5px 2px;border-bottom:1px solid #161b22;line-height:1.4;}
.s-item.done{color:#3fb950;}
.s-item.pend{color:#d29922;}
.nearby-card{background:#0d1117;border:1px solid #21262d;border-left:3px solid #30363d;
  border-radius:6px;padding:8px 10px;margin-bottom:6px;}
.nearby-card.done-card{border-left-color:#3fb950;}
.nearby-card.pend-card{border-left-color:#58a6ff;}
.nearby-card .nc-name{font-weight:700;font-size:12px;color:#58a6ff;margin-bottom:2px;}
.nearby-card .nc-info{font-size:11px;color:#8b949e;margin-top:1px;line-height:1.7;}
.nearby-card .nc-status{font-size:10px;margin-top:1px;}
.nearby-card .nc-status.done{color:#3fb950;}
.nearby-card .nc-status.pend{color:#8b949e;}
.done-btn button{border-color:#3fb950!important;color:#3fb950!important;}
.pend-btn button{border-color:#d29922!important;color:#d29922!important;}
</style>
"""

TOPBAR_HTML = f"""
<div class="topbar">
  <div>
    <div class="topbar-title">Field Survey Navigator</div>
    <div class="topbar-sub">Bristol Water — Site Survey Management</div>
  </div>
  {logo_html}
</div>
"""

st.markdown(CSS + TOPBAR_HTML, unsafe_allow_html=True)


# ─── PERSISTENCE ─────────────────────────────────────────────────────────────
def load_progress(site_names):
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE) as f:
                data = json.load(f)
            done  = {n: data.get("done",  {}).get(n, False) for n in site_names}
            notes = {n: data.get("notes", {}).get(n, "")    for n in site_names}
            return done, notes
        except Exception:
            pass
    return {n: False for n in site_names}, {n: "" for n in site_names}

def save_progress(done_dict, notes_dict):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"done": done_dict, "notes": notes_dict}, f, indent=2)
    except Exception:
        pass

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def load_sites(path):
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(4326)
    proj = gdf.to_crs(27700)
    proj["centroid"] = proj.geometry.centroid
    cents = proj["centroid"].to_crs(4326)
    gdf["lat"] = cents.y
    gdf["lon"] = cents.x
    return gdf

PATH      = os.path.join(BASE, "sites_app.geojson")
sites_raw = load_sites(PATH)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "progress_loaded" not in st.session_state:
    _names = sites_raw["Site_Name"].tolist()
    _done, _notes = load_progress(_names)
    st.session_state.done           = _done
    st.session_state.notes          = _notes
    st.session_state.progress_loaded = True

if "selected_site" not in st.session_state: st.session_state.selected_site = sites_raw["Site_Name"].iloc[0]
if "initial_load"  not in st.session_state: st.session_state.initial_load  = True
if "prev_selected" not in st.session_state: st.session_state.prev_selected = st.session_state.selected_site
if "zoom_to_site"  not in st.session_state: st.session_state.zoom_to_site  = False
if "route_mode"    not in st.session_state: st.session_state.route_mode    = None
if "route_target"  not in st.session_state: st.session_state.route_target  = None

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def fmt_time(hours):
    mins = int(hours * 60)
    return f"{mins} min" if mins < 60 else f"{mins//60}h {mins%60:02d}min"

@st.cache_data
def calc_distances(origin_lat, origin_lon, _gdf):
    """Cached per origin point. _gdf excluded from hash key (prefix _)."""
    gdf = _gdf.copy()
    origin_loc = (origin_lat, origin_lon)
    dists, dmiles, drive, walk = [], [], [], []
    for _, r in gdf.iterrows():
        d = geodesic(origin_loc, (r["lat"], r["lon"])).km
        dists.append(round(d, 2))
        dmiles.append(round(d * 0.621371, 2))
        drive.append(fmt_time(d / 50))   # 50 km/h — realistic UK average
        walk.append(fmt_time(d / 5))     # 5 km/h walking
    gdf["distance_km"]    = dists
    gdf["distance_miles"] = dmiles
    gdf["drive_fmt"]      = drive
    gdf["walk_fmt"]       = walk
    return gdf

# ─── COMPUTE ─────────────────────────────────────────────────────────────────
sel_row  = sites_raw[sites_raw["Site_Name"] == st.session_state.selected_site].iloc[0]
origin   = (sel_row["lat"], sel_row["lon"])
sites    = calc_distances(origin[0], origin[1], sites_raw)
sites_az = sites.sort_values("Site_Name").reset_index(drop=True)
filtered = sites
sel      = sites[sites["Site_Name"] == st.session_state.selected_site].iloc[0]

done_list    = [n for n, v in st.session_state.done.items() if v]
pending_list = [n for n, v in st.session_state.done.items() if not v]
done_count   = len(done_list)
total        = len(sites)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # Summary strip
    pct = int(done_count / total * 100) if total else 0
    st.markdown(f"""
    <div style="background:#0d1117;border:1px solid #21262d;border-radius:8px;
        padding:10px 14px;margin:12px 0 10px 0;display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-size:20px;font-weight:700;color:#58a6ff;line-height:1">{pct}%</div>
        <div style="font-size:9px;color:#8b949e;text-transform:uppercase;letter-spacing:1.5px;margin-top:2px">Complete</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:11px;color:#3fb950">{done_count} surveyed</div>
        <div style="font-size:11px;color:#d29922">{total - done_count} remaining</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-hdr">Search & Filter</div>', unsafe_allow_html=True)
    search = st.text_input("Search site", placeholder="Type site name...", key="search_input", label_visibility="collapsed")
    if search:
        suggestions = sites[sites["Site_Name"].str.lower().str.contains(search.lower())]["Site_Name"].sort_values().tolist()
        if suggestions:
            st.markdown(f'<div style="font-size:11px;color:#8b949e;margin:-4px 0 4px">{len(suggestions)} result(s)</div>', unsafe_allow_html=True)
            picked = st.selectbox("Suggestions", suggestions, label_visibility="collapsed", key="suggestion_box")
            if st.button("Go to site", use_container_width=True):
                st.session_state.selected_site = picked
                st.session_state.zoom_to_site  = True
                st.session_state.route_mode    = None
                st.session_state.route_target  = None
                st.rerun()
        else:
            st.markdown('<div style="font-size:11px;color:#f85149">No matches.</div>', unsafe_allow_html=True)
        filtered = sites[sites["Site_Name"].str.lower().str.contains(search.lower())]
        filtered = filtered if not filtered.empty else sites

    st.markdown('<div class="sb-hdr">Radius</div>', unsafe_allow_html=True)
    radius_miles = st.slider("Radius (miles)", 1, 150, 1, label_visibility="collapsed")
    radius_km    = radius_miles * 1.60934

    nearby_sites = sites[
        (sites["distance_miles"] <= radius_miles) &
        (sites["Site_Name"] != st.session_state.selected_site)
    ].sort_values("distance_km")

    n_nearby_done    = sum(st.session_state.done.get(n, False) for n in nearby_sites["Site_Name"])
    n_nearby_pending = len(nearby_sites) - n_nearby_done

    st.markdown(
        f'<div style="font-size:11px;color:#8b949e;margin-top:-4px;margin-bottom:6px">'
        f'{radius_miles} mi = {round(radius_km,1)} km &nbsp;·&nbsp; '
        f'<span style="color:#3fb950">{n_nearby_done} done</span> &nbsp;'
        f'<span style="color:#d29922">{n_nearby_pending} pending</span></div>',
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="sb-hdr">{len(nearby_sites)} Nearby Sites (within {radius_miles} mi)</div>', unsafe_allow_html=True)

    if nearby_sites.empty:
        st.markdown('<div style="font-size:11px;color:#8b949e;padding:4px 0">No sites in range.</div>', unsafe_allow_html=True)
    else:
        for _, row in nearby_sites.iterrows():
            name     = row["Site_Name"]
            is_done  = st.session_state.done.get(name, False)
            card_cls = "done-card" if is_done else "pend-card"
            status   = "Surveyed" if is_done else "Pending"
            st_cls   = "done" if is_done else "pend"
            st.markdown(
                f'<div class="nearby-card {card_cls}">'
                f'<div class="nc-name">{name}</div>'
                f'<div class="nc-info">{row["distance_miles"]} mi / {row["distance_km"]} km'
                f' &nbsp;·&nbsp; Drive: {row["drive_fmt"]} &nbsp;·&nbsp; Walk: {row["walk_fmt"]}</div>'
                f'<div class="nc-status {st_cls}">{status}</div></div>',
                unsafe_allow_html=True
            )
            c1, c2 = st.columns(2)
            if c1.button("By Car",  key=f"car_{name}",  use_container_width=True):
                st.session_state.route_mode   = "drive"
                st.session_state.route_target = name
                st.rerun()
            if c2.button("Walking", key=f"walk_{name}", use_container_width=True):
                st.session_state.route_mode   = "walk"
                st.session_state.route_target = name
                st.rerun()

    st.markdown('<div class="sb-hdr">Site Status</div>', unsafe_allow_html=True)
    sb_t1, sb_t2 = st.tabs(["  Surveyed  ", "  Remaining  "])
    with sb_t1:
        with st.container(height=110):
            if done_list:
                for n in sorted(done_list):
                    st.markdown(f'<div class="s-item done">✓ {n}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-size:11px;color:#8b949e;padding:6px 2px">None surveyed yet.</div>', unsafe_allow_html=True)
    with sb_t2:
        with st.container(height=110):
            if pending_list:
                for n in sorted(pending_list):
                    st.markdown(f'<div class="s-item pend">● {n}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="font-size:11px;color:#3fb950;padding:6px 2px">All done ✓</div>', unsafe_allow_html=True)

# ─── COLUMNS ─────────────────────────────────────────────────────────────────
map_col, right_col = st.columns([3, 1])

# ─── MAP ─────────────────────────────────────────────────────────────────────
with map_col:
    all_lats    = sites["lat"].tolist()
    all_lons    = sites["lon"].tolist()
    full_bounds = [[min(all_lats) - .1, min(all_lons) - .1],
                   [max(all_lats) + .1, max(all_lons) + .1]]

    m = folium.Map(tiles="OpenStreetMap", prefer_canvas=True)

    site_changed = st.session_state.selected_site != st.session_state.prev_selected
    reset_view   = st.session_state.prev_selected == "__reset__"

    if st.session_state.get("initial_load", False) or reset_view:
        m.fit_bounds(full_bounds)
    elif not site_changed and not st.session_state.zoom_to_site:
        m.fit_bounds(full_bounds)

    # ── Plugins ──
    Fullscreen(position="topleft").add_to(m)
    MiniMap(toggle_display=True, position="bottomleft", zoom_level_offset=-6).add_to(m)
    LocateControl(
        position="topleft",
        strings={"title": "Go to my location"},
        flyTo=True,
        cacheLocation=False,
        locateOptions={"enableHighAccuracy": True, "maxZoom": 15}
    ).add_to(m)

    # ── Styles for map controls ──
    _ctrl = (
        "<style>"
        ".leaflet-top.leaflet-left{top:50px!important;left:8px!important}"
        ".fullscreen-icon{background:none!important}"
        ".leaflet-control-fullscreen a{"
        "background:rgba(13,17,23,0.93)!important;"
        "border:1px solid #30363d!important;border-radius:6px!important;"
        "width:32px!important;height:32px!important;"
        "box-shadow:0 2px 8px rgba(0,0,0,.5)!important;"
        "display:flex!important;align-items:center!important;justify-content:center!important;"
        "font-size:18px!important;color:#58a6ff!important;text-decoration:none!important}"
        ".leaflet-control-fullscreen a:hover{background:#1c2a3a!important;color:#f0f6fc!important}"
        ".leaflet-control-fullscreen a::after{content:'\\26F6'!important;font-size:16px!important;color:#58a6ff!important}"
        ".leaflet-fullscreen-on .leaflet-control-fullscreen a::after{content:'\\2716'!important;font-size:14px!important;color:#f85149!important}"
        ".leaflet-control-fullscreen a img,.leaflet-control-fullscreen a span{display:none!important}"
        ".leaflet-fullscreen-on .leaflet-top.leaflet-left{top:10px!important}"
        ".leaflet-control-zoom{border:1px solid #30363d!important;border-radius:6px!important;"
        "overflow:hidden!important;box-shadow:0 2px 8px rgba(0,0,0,.5)!important;margin:0 0 6px 0!important}"
        ".leaflet-control-zoom a{width:32px!important;height:32px!important;line-height:32px!important;"
        "font-size:20px!important;font-weight:700!important;"
        "background:rgba(13,17,23,0.93)!important;color:#58a6ff!important;"
        "border-bottom:1px solid #30363d!important;"
        "display:block!important;text-align:center!important;text-decoration:none!important}"
        ".leaflet-control-zoom-out{border-bottom:none!important}"
        ".leaflet-control-zoom a:hover{background:#1c2a3a!important;color:#f0f6fc!important}"
        ".leaflet-control-fullscreen{margin:0 0 6px 0!important;clear:both!important}"
        # LocateControl styles
        ".leaflet-control-locate{margin:0 0 6px 0!important;clear:both!important}"
        ".leaflet-control-locate a{background:rgba(13,17,23,0.93)!important;"
        "border:1px solid #30363d!important;border-radius:6px!important;"
        "width:32px!important;height:32px!important;"
        "box-shadow:0 2px 8px rgba(0,0,0,.5)!important;"
        "display:flex!important;align-items:center!important;justify-content:center!important;"
        "text-decoration:none!important}"
        ".leaflet-control-locate a .fa{color:#58a6ff!important;font-size:14px!important}"
        ".leaflet-control-locate.active a .fa{color:#3fb950!important}"
        ".leaflet-control-locate.active.following a .fa{color:#d29922!important}"
        # LayerControl styles
        ".leaflet-control-layers{background:rgba(13,17,23,0.93)!important;color:#c9d1d9!important;"
        "border:1px solid #30363d!important;border-radius:6px!important;"
        "box-shadow:0 2px 8px rgba(0,0,0,.5)!important;margin:0!important;clear:both!important}"
        ".leaflet-control-layers label{color:#c9d1d9!important}"
        ".leaflet-control-layers-toggle{width:32px!important;height:32px!important}"
        ".leaflet-control-layers-expanded{padding:6px 10px!important}"
        # North arrow
        "#mc-compass{position:absolute;top:55px;right:12px;z-index:9999;"
        "width:32px;height:32px;background:rgba(13,17,23,0.93);"
        "border:1px solid #30363d;border-radius:50%;"
        "display:flex;align-items:center;justify-content:center;"
        "font-size:11px;font-weight:700;color:#58a6ff;"
        "box-shadow:0 2px 8px rgba(0,0,0,.5);pointer-events:none}"
        "</style>"
        '<div id="mc-compass">N&#8593;</div>'
    )
    m.get_root().html.add_child(folium.Element(_ctrl))

    # ── Radius circle + origin marker ──
    folium.Circle(
        location=list(origin), radius=radius_km * 1000,
        color="#f85149", weight=1.5, fill=True, fill_color="#f85149", fill_opacity=0.04,
        dash_array="8 5",
        tooltip=f"{radius_miles} miles / {round(radius_km,1)} km from selected site"
    ).add_to(m)
    folium.CircleMarker(
        location=list(origin), radius=8, color="white",
        fill=True, fill_color="#d29922", fill_opacity=1.0, weight=3,
        tooltip=f"Origin: {st.session_state.selected_site}"
    ).add_to(m)

    # ── Route line ──
    if st.session_state.route_target and st.session_state.route_mode:
        tgt_rows = sites[sites["Site_Name"] == st.session_state.route_target]
        if not tgt_rows.empty:
            tr       = tgt_rows.iloc[0]
            src_loc  = list(origin)
            tgt_loc  = [tr["lat"], tr["lon"]]
            mode     = st.session_state.route_mode
            col_line = "#d29922" if mode == "drive" else "#3fb950"
            label    = "By Car" if mode == "drive" else "Walking"
            time_str = tr["drive_fmt"] if mode == "drive" else tr["walk_fmt"]
            gm_mode  = "driving" if mode == "drive" else "walking"
            gm_url   = (f"https://www.google.com/maps/dir/?api=1"
                        f"&origin={src_loc[0]},{src_loc[1]}"
                        f"&destination={tgt_loc[0]},{tgt_loc[1]}&travelmode={gm_mode}")
            folium.PolyLine(
                locations=[src_loc, tgt_loc], color=col_line, weight=4,
                opacity=.9, dash_array="10 6" if mode == "walk" else None,
                tooltip=f"{label}: {tr['distance_km']} km | {time_str}"
            ).add_to(m)
            mid = [(src_loc[0] + tgt_loc[0]) / 2, (src_loc[1] + tgt_loc[1]) / 2]
            folium.Marker(
                location=mid,
                icon=folium.DivIcon(
                    html=f'<div style="background:{col_line};color:white;padding:3px 8px;'
                         f'border-radius:4px;font-size:11px;font-weight:700;white-space:nowrap">'
                         f'{label}: {tr["distance_miles"]} mi | {time_str}</div>',
                    icon_size=(200, 24), icon_anchor=(100, 12)),
                popup=folium.Popup(
                    f'<div style="font-family:Inter,sans-serif;font-size:12px;min-width:190px;line-height:1.9">'
                    f'<b>{label}</b><br>From: {st.session_state.selected_site}<br>'
                    f'To: {st.session_state.route_target}<br>'
                    f'Distance: {tr["distance_km"]} km / {tr["distance_miles"]} mi<br>'
                    f'Est. Time: {time_str}<br><br>'
                    f'<a href="{gm_url}" target="_blank" style="color:#58a6ff;font-weight:600">'
                    f'Open in Google Maps ↗</a></div>', max_width=240)
            ).add_to(m)
            m.fit_bounds([
                [min(src_loc[0], tgt_loc[0]) - .02, min(src_loc[1], tgt_loc[1]) - .02],
                [max(src_loc[0], tgt_loc[0]) + .02, max(src_loc[1], tgt_loc[1]) + .02]
            ])

    # ── Feature groups ──
    fg_out  = folium.FeatureGroup(name="Out of Range",  show=True)
    fg_near = folium.FeatureGroup(name="Within Radius", show=True)
    fg_done = folium.FeatureGroup(name="Surveyed",      show=True)
    fg_sel  = folium.FeatureGroup(name="Selected",      show=True)

    for _, row in sites.iterrows():
        name    = row["Site_Name"]
        is_sel  = name == st.session_state.selected_site
        is_done = st.session_state.done.get(name, False)
        is_near = row["distance_miles"] <= radius_miles
        area    = row.get("Area_Ha", "N/A")
        has_note = bool(st.session_state.notes.get(name, "").strip())
        note_badge = " 📝" if has_note else ""

        if is_done:   fill, border, wt, fg = "#3fb950", "#2ea043", 2, fg_done
        elif is_sel:  fill, border, wt, fg = "#d29922", "#bb8009", 3, fg_sel
        elif is_near: fill, border, wt, fg = "#58a6ff", "#388bfd", 2, fg_near
        else:         fill, border, wt, fg = "#30363d", "#21262d", 1, fg_out

        popup_html = (
            f'<div style="font-family:Inter,sans-serif;min-width:210px;border-radius:6px;overflow:hidden">'
            f'<div style="background:#161b22;color:#58a6ff;padding:8px 12px;font-weight:700;'
            f'font-size:13px;border-bottom:1px solid #30363d">{name}{note_badge}</div>'
            f'<div style="padding:8px 12px;background:#0d1117;color:#c9d1d9;line-height:2;font-size:12px">'
            f'Area: <b>{area} ha</b><br>'
            f'Distance: <b>{row["distance_km"]} km</b> / {row["distance_miles"]} mi<br>'
            f'Drive: <b>{row["drive_fmt"]}</b><br>Walk: <b>{row["walk_fmt"]}</b><br>'
            f'Status: <b style="color:{"#3fb950" if is_done else "#d29922"}">{"Surveyed" if is_done else "Pending"}</b>'
            + (f'<br><br><span style="color:#8b949e;font-size:11px">{st.session_state.notes[name]}</span>'
               if has_note else "") +
            f'</div></div>'
        )
        folium.GeoJson(
            row.geometry,
            tooltip=folium.Tooltip(
                f"{name} | {row['distance_miles']} mi | Drive: {row['drive_fmt']} | Walk: {row['walk_fmt']}",
                sticky=True
            ),
            popup=folium.Popup(popup_html, max_width=280),
            style_function=lambda x, f=fill, b=border, w=wt: {
                "fillColor": f, "color": b, "weight": w, "fillOpacity": .65
            },
            highlight_function=lambda x: {"weight": 4, "fillOpacity": .9}
        ).add_to(fg)

    fg_out.add_to(m)
    fg_near.add_to(m)
    fg_done.add_to(m)
    fg_sel.add_to(m)

    folium.LayerControl(position="topleft", collapsed=True).add_to(m)

    # ── Zoom to selected site ──
    if (site_changed or st.session_state.zoom_to_site) and \
       not st.session_state.route_mode and not reset_view and \
       not st.session_state.get("initial_load", False):
        sg   = sites[sites["Site_Name"] == st.session_state.selected_site].geometry.iloc[0]
        b    = sg.bounds
        span = max(b[2] - b[0], b[3] - b[1])
        pad  = max(0.003, min(0.02, span * 2.0))
        m.fit_bounds([[b[1] - pad, b[0] - pad], [b[3] + pad, b[2] + pad]])

    st.session_state.prev_selected = st.session_state.selected_site
    st.session_state.zoom_to_site  = False
    st.session_state.initial_load  = False

    map_data = st_folium(m, width=None, height=MAP_H, key="main_map",
                         returned_objects=["last_object_clicked"])

    if map_data and map_data.get("last_object_clicked"):
        click = map_data["last_object_clicked"]
        clat, clon = click.get("lat"), click.get("lng")
        if clat and clon:
            dists   = sites.apply(lambda r: geodesic((clat, clon), (r["lat"], r["lon"])).km, axis=1)
            nearest = sites.loc[dists.idxmin(), "Site_Name"]
            if nearest != st.session_state.selected_site:
                st.session_state.selected_site = nearest
                st.session_state.zoom_to_site  = True
                st.session_state.route_mode    = None
                st.session_state.route_target  = None
                st.rerun()

# ─── RIGHT PANEL ─────────────────────────────────────────────────────────────
with right_col:
    # ── Progress ──
    st.markdown('<div class="sec-hdr">Progress</div>', unsafe_allow_html=True)
    st.progress(done_count / total if total else 0)
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="val">{total}</div><div class="lbl">Total</div></div>
        <div class="metric-box"><div class="val green">{done_count}</div><div class="lbl">Done</div></div>
        <div class="metric-box"><div class="val orange">{total - done_count}</div><div class="lbl">Left</div></div>
    </div>""", unsafe_allow_html=True)

    # ── Selected Site ──
    sel_name = sel["Site_Name"]
    area     = sel.get("Area_Ha", "N/A")
    is_sel_done = st.session_state.done.get(sel_name, False)
    status   = "Surveyed" if is_sel_done else "Pending"
    scol     = "#3fb950" if is_sel_done else "#d29922"

    st.markdown('<div class="sec-hdr">Selected Site</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sel-card">
        <div class="sc-name">{sel_name}</div>
        <div class="sc-row">
            Area: <b>{area} ha</b><br>
            Dist: <b>{sel['distance_km']} km</b> / {sel['distance_miles']} mi<br>
            Drive: <b>{sel['drive_fmt']}</b> &nbsp;·&nbsp; Walk: <b>{sel['walk_fmt']}</b><br>
            Status: <b style="color:{scol}">{status}</b>
        </div>
    </div>""", unsafe_allow_html=True)

    # Quick toggle button
    btn_label = "✓ Mark as Surveyed" if not is_sel_done else "↩ Mark as Pending"
    btn_div   = "done-btn" if not is_sel_done else "pend-btn"
    st.markdown(f'<div class="{btn_div}">', unsafe_allow_html=True)
    if st.button(btn_label, use_container_width=True, key="btn_toggle"):
        st.session_state.done[sel_name] = not is_sel_done
        save_progress(st.session_state.done, st.session_state.notes)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Notes
    def _save_note():
        st.session_state.notes[sel_name] = st.session_state["note_input"]
        save_progress(st.session_state.done, st.session_state.notes)

    with st.expander("📝 Field Notes", expanded=bool(st.session_state.notes.get(sel_name, "").strip())):
        st.text_area(
            "notes",
            value=st.session_state.notes.get(sel_name, ""),
            height=72,
            key="note_input",
            on_change=_save_note,
            placeholder="Add observations, access notes...",
            label_visibility="collapsed"
        )

    # ── Jump to Site ──
    st.markdown('<div class="jump-hdr">Jump to Site</div>', unsafe_allow_html=True)
    site_list_az = sorted(filtered["Site_Name"].tolist())
    idx     = site_list_az.index(st.session_state.selected_site) if st.session_state.selected_site in site_list_az else 0
    new_sel = st.selectbox("Site", site_list_az, index=idx, label_visibility="collapsed")
    if new_sel != st.session_state.selected_site:
        st.session_state.selected_site = new_sel
        st.session_state.zoom_to_site  = True
        st.session_state.route_mode    = None
        st.session_state.route_target  = None
        st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("Reset View",  use_container_width=True, key="btn_reset"):
        st.session_state.zoom_to_site  = False
        st.session_state.route_mode    = None
        st.session_state.route_target  = None
        st.session_state.prev_selected = "__reset__"
        st.rerun()
    if c2.button("Clear Route", use_container_width=True, key="btn_clr"):
        st.session_state.route_mode   = None
        st.session_state.route_target = None
        st.rerun()

    # ── Export ──
    st.markdown('<div class="sec-hdr">Export</div>', unsafe_allow_html=True)
    export_df = pd.DataFrame({
        "Site":             sites_az["Site_Name"].tolist(),
        "Area (ha)":        [sites_az.loc[i, "Area_Ha"] if "Area_Ha" in sites_az.columns else "N/A"
                             for i in sites_az.index],
        "Distance (km)":    sites_az["distance_km"].tolist(),
        "Distance (miles)": sites_az["distance_miles"].tolist(),
        "Drive Time":       sites_az["drive_fmt"].tolist(),
        "Walk Time":        sites_az["walk_fmt"].tolist(),
        "Status":           [("Surveyed" if st.session_state.done.get(n) else "Pending")
                             for n in sites_az["Site_Name"]],
        "Notes":            [st.session_state.notes.get(n, "") for n in sites_az["Site_Name"]],
    })
    st.download_button(
        "⬇ Export Progress CSV",
        export_df.to_csv(index=False),
        file_name="survey_progress.csv",
        mime="text/csv",
        use_container_width=True
    )

