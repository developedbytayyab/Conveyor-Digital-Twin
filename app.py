
from __future__ import annotations

import json
import os
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

from simulator import generate_sensor_data
from ml_detector import detect_anomalies
from optimizer import recommend_speed
from reports import csv_bytes, pdf_report


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Conveyor Digital Twin",
    page_icon="🏭",
    layout="wide",
)


# --------------------------------------------------
# OPTIONAL PASSWORD PROTECTION
# --------------------------------------------------
def require_app_password() -> None:
    expected = os.environ.get("TWIN_APP_PASSWORD", "").strip()

    if not expected:
        st.sidebar.warning(
            "App password not configured. "
            "Set TWIN_APP_PASSWORD before internet exposure."
        )
        return

    if st.session_state.get("twin_authenticated", False):
        return

    st.title("🔐 Conveyor Digital Twin — Sign in")
    entered = st.text_input("App password", type="password")

    if st.button("Sign in", type="primary"):
        if entered and entered == expected:
            st.session_state["twin_authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()


require_app_password()


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🏭 Conveyor Digital Twin")
st.caption(
    "3D Simulation · AI Anomaly Detection · Predictive Maintenance "
    "· Self-Optimization"
)


# --------------------------------------------------
# SIDEBAR CONTROLS
# --------------------------------------------------
with st.sidebar:
    st.header("Simulation Controls")

    n = st.slider("Samples", 100, 1000, 300, 50)
    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=100000,
        value=7,
    )
    contamination = st.slider(
        "AI anomaly sensitivity",
        0.01,
        0.20,
        0.06,
        0.01,
    )
    speed_control = st.slider(
        "Nominal belt speed (m/s)",
        0.5,
        1.8,
        1.2,
        0.1,
    )

    run = st.button(
        "Run simulation",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "Simulation only. No physical PLC or conveyor is controlled."
    )


# --------------------------------------------------
# SIMULATION DATA
# --------------------------------------------------
if "sim_data" not in st.session_state or run:
    st.session_state.sim_data = generate_sensor_data(
        int(n), int(seed)
    )

raw = st.session_state.sim_data.copy()

raw["belt_speed_m_s"] = (
    raw["belt_speed_m_s"] * speed_control / 1.2
).clip(0.5, 1.8)

raw["package_rate_min"] = (
    raw["package_rate_min"] * speed_control / 1.2
)

try:
    data = detect_anomalies(raw, float(contamination))
except ValueError as exc:
    st.error(f"Anomaly detection error: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Could not process simulation data: {exc}")
    st.stop()

if data.empty:
    st.error("Simulation returned no data. Run the simulation again.")
    st.stop()

latest = data.iloc[-1]

health = max(
    0,
    min(
        100,
        round(
            100
            - data["anomaly_score"].tail(30).mean() * 100
            - data["is_anomaly"].tail(30).mean() * 35
        ),
    ),
)


# --------------------------------------------------
# TOP METRICS
# --------------------------------------------------
a, b, c, d = st.columns(4)

a.metric("Machine Health", f"{health}/100")
b.metric("Detected Anomalies", int(data["is_anomaly"].sum()))
c.metric("Latest Temperature", f"{latest.temperature_c:.1f} °C")
d.metric("Throughput", f"{latest.package_rate_min:.1f} pkg/min")


# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "3D Digital Twin",
        "Live Sensors & AI",
        "Maintenance & Optimization",
        "Reports & Event Log",
        "Local LLM Copilot",
    ]
)


# ==================================================
# TAB 1: 3D CONVEYOR DIGITAL TWIN
# ==================================================
with tab1:
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("Twin Status")

        st.write(
            f"**Motor:** "
            f"{'⚠️ Inspect' if latest.is_anomaly else '🟢 Running'}"
        )
        st.write(f"**Belt speed:** {latest.belt_speed_m_s:.2f} m/s")
        st.write(f"**Vibration:** {latest.vibration_mm_s:.2f} mm/s")
        st.write(
            f"**AI status:** "
            f"{'🔴 Anomaly' if latest.is_anomaly else '🟢 Normal'}"
        )

        if st.button(
            "▶ Advance Simulation Step",
            type="primary",
            key="advance_3d",
            use_container_width=True,
        ):
            new_seed = int(time.time()) % 100000
            st.session_state.sim_data = generate_sensor_data(
                int(n), int(seed) + new_seed
            )
            st.rerun()

        st.info(
            "Packages update when you advance the simulation. "
            "The visualization is illustrative, not a calibrated CAD model."
        )

    with col1:
        fig = go.Figure()

        # Conveyor belt surface
        belt_x = np.linspace(0, 10, 30)
        belt_y = np.linspace(-0.75, 0.75, 8)
        X, Y = np.meshgrid(belt_x, belt_y)
        Z = np.full_like(X, 0.16)

        fig.add_trace(
            go.Surface(
                x=X,
                y=Y,
                z=Z,
                colorscale=[
                    [0, "#26384a"],
                    [1, "#526477"],
                ],
                showscale=False,
                name="Conveyor Belt",
                hoverinfo="skip",
            )
        )

        # Conveyor side rails
        for rail_y in [-0.88, 0.88]:
            fig.add_trace(
                go.Scatter3d(
                    x=[0, 10],
                    y=[rail_y, rail_y],
                    z=[0.25, 0.25],
                    mode="lines",
                    line=dict(color="#f59e0b", width=9),
                    name="Side Rail",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # Conveyor support legs
        for support_x in [0.5, 3, 5.5, 8, 9.5]:
            for support_y in [-0.7, 0.7]:
                fig.add_trace(
                    go.Scatter3d(
                        x=[support_x, support_x],
                        y=[support_y, support_y],
                        z=[-0.8, 0.12],
                        mode="lines",
                        line=dict(color="#6b7280", width=7),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

        # Rollers represented as cylindrical rings
        theta = np.linspace(0, 2 * np.pi, 32)

        for roller_x in np.arange(0.35, 10, 0.8):
            roller_y = np.linspace(-0.78, 0.78, 8)
            T, YY = np.meshgrid(theta, roller_y)

            RX = roller_x + 0.12 * np.sin(T)
            RZ = 0.16 + 0.12 * np.cos(T)

            fig.add_trace(
                go.Surface(
                    x=RX,
                    y=YY,
                    z=RZ,
                    colorscale=[
                        [0, "#9ca3af"],
                        [1, "#e5e7eb"],
                    ],
                    showscale=False,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

        # Package positions depend on speed and simulation step
        speed = float(latest.belt_speed_m_s)

        if "twin_step" not in st.session_state:
            st.session_state.twin_step = 0

        positions = [
            (
                i * 2.2
                + speed * 0.7 * st.session_state.twin_step
            ) % 8.8 + 0.6
            for i in range(4)
        ]

        # Cuboid faces
        faces = [
            (0, 1, 2), (0, 2, 3),
            (4, 6, 5), (4, 7, 6),
            (0, 4, 5), (0, 5, 1),
            (1, 5, 6), (1, 6, 2),
            (2, 6, 7), (2, 7, 3),
            (3, 7, 4), (3, 4, 0),
        ]

        for i, package_x in enumerate(positions):
            x0, x1 = package_x - 0.35, package_x + 0.35
            y0, y1 = -0.3, 0.3
            z0, z1 = 0.30, 0.90

            vertices = [
                (x0, y0, z0),
                (x1, y0, z0),
                (x1, y1, z0),
                (x0, y1, z0),
                (x0, y0, z1),
                (x1, y0, z1),
                (x1, y1, z1),
                (x0, y1, z1),
            ]

            color = (
                "#ef4444"
                if latest.is_anomaly and i == 0
                else "#f59e0b"
            )

            fig.add_trace(
                go.Mesh3d(
                    x=[v[0] for v in vertices],
                    y=[v[1] for v in vertices],
                    z=[v[2] for v in vertices],
                    i=[f[0] for f in faces],
                    j=[f[1] for f in faces],
                    k=[f[2] for f in faces],
                    color=color,
                    opacity=0.98,
                    name=f"Package {i + 1}",
                    showlegend=False,
                    hovertemplate=(
                        f"Package {i + 1}<extra></extra>"
                    ),
                )
            )

        # Motor at conveyor end
        fig.add_trace(
            go.Scatter3d(
                x=[10.2],
                y=[0],
                z=[0.3],
                mode="markers",
                marker=dict(
                    size=13,
                    color=(
                        "red" if latest.is_anomaly else "#22c55e"
                    ),
                    symbol="diamond",
                ),
                name="Motor Status",
                hovertemplate="Motor<extra></extra>",
            )
        )

        # Layout and camera
        fig.update_layout(
            height=570,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            scene=dict(
                xaxis_title="Conveyor Length (m)",
                yaxis_title="Width (m)",
                zaxis_title="Height (m)",
                xaxis=dict(range=[-0.5, 11], backgroundcolor="#f8fafc"),
                yaxis=dict(range=[-1.3, 1.3], backgroundcolor="#f8fafc"),
                zaxis=dict(range=[-1, 1.8], backgroundcolor="#f8fafc"),
                aspectmode="manual",
                aspectratio=dict(x=2.5, y=1, z=0.7),
                camera=dict(
                    eye=dict(x=1.6, y=1.6, z=1.1)
                ),
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key="conveyor_3d_scene",
            config={
                "displayModeBar": True,
                "scrollZoom": True,
            },
        )

        st.caption(
            "Orange packages: normal simulated parcels. "
            "Red package/motor: anomaly indicator. "
            "Use the mouse to rotate and zoom the 3D scene."
        )


# ==================================================
# TAB 2: LIVE SENSORS AND AI
# ==================================================
with tab2:
    metric = st.selectbox(
        "Sensor Trend",
        [
            "temperature_c",
            "vibration_mm_s",
            "motor_current_a",
            "belt_speed_m_s",
            "package_rate_min",
        ],
    )

    chart = go.Figure()

    chart.add_trace(
        go.Scatter(
            x=data.timestamp,
            y=data[metric],
            mode="lines",
            name=metric.replace("_", " ").title(),
        )
    )

    bad = data[data.is_anomaly]

    chart.add_trace(
        go.Scatter(
            x=bad.timestamp,
            y=bad[metric],
            mode="markers",
            name="AI Anomaly",
            marker=dict(color="red", size=8),
        )
    )

    chart.update_layout(
        height=370,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="Time",
    )

    st.plotly_chart(chart, use_container_width=True)

    st.dataframe(
        data.tail(25),
        use_container_width=True,
        hide_index=True,
    )


# ==================================================
# TAB 3: MAINTENANCE AND OPTIMIZATION
# ==================================================
with tab3:
    rec = recommend_speed(
        float(latest.belt_speed_m_s),
        float(latest.temperature_c),
        float(latest.vibration_mm_s),
    )

    x, y, z = st.columns(3)

    x.metric(
        "Recommended Speed",
        f"{rec['recommended_speed_m_s']:.2f} m/s",
        f"{rec['speed_change_pct']:+.1f}%",
    )

    y.metric(
        "Maintenance Priority",
        (
            "Critical"
            if latest.severity == "Critical"
            else ("Inspect" if latest.is_anomaly else "Routine")
        ),
    )

    z.metric("Estimated Health", f"{health}/100")

    st.info(rec["reason"])

    if latest.is_anomaly:
        st.warning(
            "Unusual simulated sensor behavior detected. "
            "Inspect the simulated motor/bearing readings."
        )
    else:
        st.success(
            "No anomaly in the latest sample. Continue monitoring trends."
        )

    st.caption(
        "Optimization is a simulated recommendation, not a command "
        "to physical machinery. Maintenance estimates are heuristic."
    )


# ==================================================
# TAB 4: REPORTS AND EVENT LOG
# ==================================================
with tab4:
    events = (
        data[data.is_anomaly]
        .copy()
        .sort_values("timestamp", ascending=False)
    )

    st.subheader("Anomaly Event Log")

    st.dataframe(
        events,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download CSV Report",
        data=csv_bytes(data),
        file_name="conveyor_twin_report.csv",
        mime="text/csv",
    )

    st.download_button(
        "Download PDF Report",
        data=pdf_report(data),
        file_name="conveyor_twin_report.pdf",
        mime="application/pdf",
    )

    st.subheader("Simulation Summary")

    st.write(
        {
            "samples": len(data),
            "anomaly_count": int(data.is_anomaly.sum()),
            "critical_count": int(
                (data.severity == "Critical").sum()
            ),
            "mean_temperature_c": round(
                float(data.temperature_c.mean()), 2
            ),
            "mean_vibration_mm_s": round(
                float(data.vibration_mm_s.mean()), 2
            ),
        }
    )


# ==================================================
# TAB 5: LOCAL OLLAMA LLM COPILOT
# ==================================================
with tab5:
    st.subheader("🤖 Local LLM Maintenance Copilot")
    st.caption(
        "Responses are generated by an Ollama model on the configured PC."
    )

    ollama_url = st.text_input(
        "Ollama URL",
        value=os.environ.get(
            "OLLAMA_HOST", "http://127.0.0.1:11434"
        ),
    )

    model_name = st.text_input(
        "Ollama Model",
        value=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
    )

    recommendation = recommend_speed(
        float(latest.belt_speed_m_s),
        float(latest.temperature_c),
        float(latest.vibration_mm_s),
    )

    context = {
        "latest_sensor_sample": {
            k: (
                str(v)
                if k == "timestamp"
                else (
                    float(v)
                    if hasattr(v, "__float__")
                    else str(v)
                )
            )
            for k, v in latest.to_dict().items()
        },
        "machine_health_score": int(health),
        "anomaly_count_in_window": int(data["is_anomaly"].sum()),
        "latest_sample_is_anomaly": bool(latest["is_anomaly"]),
        "maintenance_recommendation": recommendation,
        "important_limitations": (
            "Sensor data is simulated. Recommendations are advisory. "
            "No hardware is connected."
        ),
    }

    if "llm_messages" not in st.session_state:
        st.session_state.llm_messages = []

    for message in st.session_state.llm_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask about anomalies, maintenance, or optimization..."
    )

    if prompt:
        st.session_state.llm_messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        system_prompt = (
            "You are a careful industrial conveyor maintenance assistant. "
            "Answer in the user's language. Use the supplied JSON context. "
            "Distinguish observations from hypotheses. The data is simulated. "
            "Never recommend bypassing guards, interlocks, emergency stops, "
            "or safety procedures. For critical anomalies, recommend safe "
            "shutdown according to site procedures and qualified inspection.\n\n"
            "CURRENT SIMULATION CONTEXT:\n"
            + json.dumps(context, ensure_ascii=False, default=str)
        )

        ollama_messages = [
            {"role": "system", "content": system_prompt}
        ]

        ollama_messages.extend(
            {
                "role": m["role"],
                "content": m["content"],
            }
            for m in st.session_state.llm_messages[-10:]
        )

        with st.chat_message("assistant"):
            try:
                with st.spinner(
                    f"Contacting Ollama model {model_name}..."
                ):
                    response = requests.post(
                        ollama_url.rstrip("/") + "/api/chat",
                        json={
                            "model": model_name,
                            "messages": ollama_messages,
                            "stream": False,
                        },
                        timeout=180,
                    )

                    response.raise_for_status()

                    answer = (
                        response.json()
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    if not answer:
                        answer = (
                            "Ollama returned an empty response. "
                            "Check the model name and Ollama logs."
                        )

                    st.markdown(answer)

                    st.session_state.llm_messages.append(
                        {"role": "assistant", "content": answer}
                    )

            except requests.exceptions.ConnectionError:
                answer = (
                    "Ollama se connection nahi ho saka. Confirm karein "
                    "Ollama running hai aur model download ho chuka hai."
                )
                st.error(answer)
                st.session_state.llm_messages.append(
                    {"role": "assistant", "content": answer}
                )

            except requests.exceptions.Timeout:
                answer = (
                    "Model response timed out. Try a smaller model "
                    "or check PC resources."
                )
                st.error(answer)
                st.session_state.llm_messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as exc:
                answer = f"Ollama request failed: {exc}"
                st.error(answer)
                st.session_state.llm_messages.append(
                    {"role": "assistant", "content": answer}
                )

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("Test Ollama Connection"):
            try:
                response = requests.get(
                    ollama_url.rstrip("/") + "/api/tags",
                    timeout=8,
                )
                response.raise_for_status()

                models = [
                    m.get("name", "")
                    for m in response.json().get("models", [])
                ]

                st.success(
                    "Ollama reachable. Models: "
                    + (", ".join(models) if models else "No models found")
                )

            except Exception as exc:
                st.error(f"Connection test failed: {exc}")

    with col_b:
        if st.button("Clear Chat"):
            st.session_state.llm_messages = []
            st.rerun()
