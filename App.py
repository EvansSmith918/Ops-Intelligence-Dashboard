import random
import time
from datetime import datetime, timedelta

import pandas as pd
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="Operational Intelligence System", layout="wide")

st.title("Real-Time Operational Intelligence System")
st.caption(
    "Monitoring geographically grounded live event activity around critical hubs in real time"
)

EVENT_SKIP_PROBABILITY = 0.45

HUBS = {
    "Jackson Air Operations": {
        "lat": 32.3112,
        "lon": -90.0759,
        "priority": 1.20,
    },
    "Gulfport Port Access": {
        "lat": 30.3674,
        "lon": -89.0928,
        "priority": 1.35,
    },
    "Meridian Rail Junction": {
        "lat": 32.3643,
        "lon": -88.7037,
        "priority": 1.05,
    },
    "Hattiesburg Logistics Hub": {
        "lat": 31.3271,
        "lon": -89.2903,
        "priority": 1.00,
    },
    "Vicksburg River Crossing": {
        "lat": 32.3526,
        "lon": -90.8779,
        "priority": 0.95,
    },
}

INCIDENT_TYPES = {
    "Perimeter Breach": 1.50,
    "Unauthorized Access": 1.35,
    "Vehicle Anomaly": 1.10,
    "Unusual Movement": 0.95,
    "Signal Interruption": 1.20,
}

INCIDENT_SELECTION_WEIGHTS = {
    "Perimeter Breach": 1.1,
    "Unauthorized Access": 1.0,
    "Vehicle Anomaly": 0.9,
    "Unusual Movement": 1.2,
    "Signal Interruption": 0.8,
}

SEVERITY_COLORS = {
    "LOW": [52, 152, 219, 180],
    "MEDIUM": [241, 196, 15, 190],
    "HIGH": [231, 76, 60, 210],
}

if "events" not in st.session_state:
    st.session_state.events = []

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = {}

if "system_started_at" not in st.session_state:
    st.session_state.system_started_at = datetime.now()

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

st.sidebar.title("System Status")
st.sidebar.success("System Online")
st.sidebar.markdown("### System Mode")
st.sidebar.write("Automated Monitoring")
st.sidebar.markdown("### Data Source")
st.sidebar.write("Simulated live event stream anchored to real geographic hubs")

st.sidebar.markdown("### Controls")
st.session_state.auto_refresh = st.sidebar.toggle(
    "Auto Refresh",
    value=st.session_state.auto_refresh
)
manual_step = st.sidebar.button("Generate One Event")


def jitter_coordinate(value: float, spread: float = 0.018) -> float:
    return value + random.uniform(-spread, spread)


def select_hub_name() -> str:
    hub_names = list(HUBS.keys())
    weights = [HUBS[name]["priority"] for name in hub_names]
    return random.choices(hub_names, weights=weights, k=1)[0]


def select_incident_type() -> str:
    incident_names = list(INCIDENT_SELECTION_WEIGHTS.keys())
    selection_weights = list(INCIDENT_SELECTION_WEIGHTS.values())
    return random.choices(incident_names, weights=selection_weights, k=1)[0]


def generate_event():
    if random.random() < EVENT_SKIP_PROBABILITY:
        return None

    hub_name = select_hub_name()
    hub = HUBS[hub_name]
    incident_type = select_incident_type()
    severity_seed = INCIDENT_TYPES[incident_type] * hub["priority"]

    if severity_seed >= 1.65:
        baseline_level = "HIGH"
    elif severity_seed >= 1.15:
        baseline_level = "MEDIUM"
    else:
        baseline_level = "LOW"

    return {
        "time": datetime.now(),
        "hub": hub_name,
        "incident_type": incident_type,
        "lat": jitter_coordinate(hub["lat"]),
        "lon": jitter_coordinate(hub["lon"]),
        "hub_priority": hub["priority"],
        "incident_weight": INCIDENT_TYPES[incident_type],
        "baseline_level": baseline_level,
    }


if st.session_state.auto_refresh or manual_step:
    new_event = generate_event()
    if new_event is not None:
        st.session_state.events.append(new_event)

cutoff = datetime.now() - timedelta(minutes=10)
st.session_state.events = [
    event for event in st.session_state.events if event["time"] > cutoff
]

events_df = pd.DataFrame(st.session_state.events)

if not events_df.empty:
    events_df["time"] = pd.to_datetime(events_df["time"])

alerts = []
current_time = datetime.now()
hub_risk_rows = []

if not events_df.empty:
    for hub_name, hub in HUBS.items():
        hub_events = events_df[events_df["hub"] == hub_name].copy()
        if hub_events.empty:
            continue

        weighted_score = 0.0

        for _, row in hub_events.iterrows():
            minutes_ago = (current_time - row["time"]).total_seconds() / 60
            recency_factor = max(0.30, 1.0 - (minutes_ago / 10))
            weighted_score += (
                12
                * row["incident_weight"]
                * row["hub_priority"]
                * recency_factor
            )

        event_count = len(hub_events)

        if weighted_score >= 55:
            level = "HIGH"
        elif weighted_score >= 28:
            level = "MEDIUM"
        elif weighted_score >= 14:
            level = "LOW"
        else:
            level = ""

        if level:
            last_time = st.session_state.last_alert_time.get(hub_name)
            if last_time is None or (current_time - last_time).total_seconds() > 12:
                alerts.append(
                    f"{level} ALERT: Elevated activity detected near {hub_name} "
                    f"({event_count} recent events, weighted score {int(weighted_score)})"
                )
                st.session_state.last_alert_time[hub_name] = current_time

        hub_risk_rows.append(
            {
                "hub": hub_name,
                "event_count": event_count,
                "weighted_score": weighted_score,
                "lat": hub["lat"],
                "lon": hub["lon"],
                "display_level": level if level else "NORMAL",
            }
        )

risk_df = pd.DataFrame(hub_risk_rows)

active_incidents = 0 if events_df.empty else len(events_df)
active_alerts = len(alerts)

st.sidebar.metric("Active Incidents", active_incidents)
st.sidebar.metric("Active Alerts", active_alerts)
st.sidebar.metric(
    "Monitoring Uptime",
    f"{int((datetime.now() - st.session_state.system_started_at).total_seconds() // 60)} min",
)

overall_threat_score = 0
if not risk_df.empty:
    overall_threat_score = min(int(risk_df["weighted_score"].sum() / 3.2), 100)

top_left, top_right = st.columns([1.35, 1])

with top_left:
    st.subheader("Live Incident Feed")

    if events_df.empty:
        st.info("Awaiting incoming incident activity")
    else:
        feed_df = (
            events_df.sort_values("time", ascending=False)
            .tail(12)
            .copy()
        )
        feed_df["time"] = feed_df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        feed_df = feed_df[
            ["time", "hub", "incident_type", "baseline_level"]
        ].rename(
            columns={
                "hub": "location",
                "incident_type": "incident",
                "baseline_level": "severity",
            }
        )
        st.dataframe(feed_df, use_container_width=True, hide_index=True)

with top_right:
    st.subheader("Alerts")

    if alerts:
        for alert in alerts:
            if alert.startswith("HIGH"):
                st.error(alert)
            elif alert.startswith("MEDIUM"):
                st.warning(alert)
            else:
                st.info(alert)
    else:
        st.success("System stable: no abnormal activity detected")

metric_col1, metric_col2 = st.columns(2)

with metric_col1:
    st.markdown("### Threat Level")
    st.metric("Overall Threat Level", f"{overall_threat_score}%")

with metric_col2:
    st.markdown("### Highest Risk Hub")
    if not risk_df.empty:
        top_hub = risk_df.sort_values("weighted_score", ascending=False).iloc[0]
        st.metric("Current Focus Area", top_hub["hub"])
    else:
        st.metric("Current Focus Area", "No active concentration")

st.markdown("### Geographic Activity Map")
st.caption("Pause auto-refresh to inspect map activity, then resume live monitoring when ready")

if not events_df.empty:
    map_df = events_df.copy()

    def event_color(level: str):
        return SEVERITY_COLORS.get(level, [120, 120, 120, 150])

    map_df["color"] = map_df["baseline_level"].apply(event_color)
    map_df["tooltip_text"] = (
        "Location: " + map_df["hub"]
        + "\nIncident: " + map_df["incident_type"]
        + "\nTime: " + map_df["time"].dt.strftime("%H:%M:%S")
    )

    event_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius=1800,
        pickable=True,
        opacity=0.65,
        stroked=True,
        filled=True,
        radius_min_pixels=4,
        radius_max_pixels=18,
        line_width_min_pixels=1,
    )

    hub_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame(
            [
                {
                    "hub": hub_name,
                    "lat": hub_data["lat"],
                    "lon": hub_data["lon"],
                }
                for hub_name, hub_data in HUBS.items()
            ]
        ),
        get_position="[lon, lat]",
        get_fill_color=[220, 220, 220, 170],
        get_radius=2600,
        pickable=True,
        stroked=True,
        filled=True,
        radius_min_pixels=5,
        radius_max_pixels=9,
        line_width_min_pixels=1,
    )

    view_state = pdk.ViewState(
        latitude=31.6,
        longitude=-89.6,
        zoom=6.1,
        pitch=0,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v11",
            initial_view_state=view_state,
            layers=[hub_layer, event_layer],
            tooltip={"text": "{tooltip_text}"},
        ),
        use_container_width=True,
    )
else:
    st.info("Map will populate as incident activity arrives")

bottom_left, bottom_right = st.columns(2)

with bottom_left:
    st.markdown("### Activity Over Time")
    if not events_df.empty:
        timeline_df = events_df.copy()
        timeline_df["second_bucket"] = timeline_df["time"].dt.floor("10s")
        counts = timeline_df.groupby("second_bucket").size().rename("incidents")
        st.line_chart(counts)
    else:
        st.info("No timeline data available yet")

with bottom_right:
    st.markdown("### Incident Type Distribution")
    if not events_df.empty:
        type_counts = events_df["incident_type"].value_counts()
        st.bar_chart(type_counts)
    else:
        st.info("No incident distribution available yet")

st.markdown("### Hub Risk Summary")
if not risk_df.empty:
    display_risk_df = risk_df.copy()
    display_risk_df["weighted_score"] = display_risk_df["weighted_score"].round(1)
    display_risk_df = display_risk_df[
        ["hub", "event_count", "weighted_score", "display_level"]
    ].rename(
        columns={
            "hub": "hub",
            "event_count": "recent_events",
            "weighted_score": "risk_score",
            "display_level": "status_level",
        }
    )
    st.dataframe(display_risk_df, use_container_width=True, hide_index=True)
else:
    st.info("Risk summary will appear once events are detected")

if st.session_state.auto_refresh:
    time.sleep(4)
    st.rerun()