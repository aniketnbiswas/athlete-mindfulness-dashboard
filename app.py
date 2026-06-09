import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Athlete Mindfulness & Performance Tracker",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* App background */
    .stApp {
        background-color: #0D1117;
        color: #E6EDF3;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #21262D;
    }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #58A6FF;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
        border: 1px solid #21262D;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 4px; height: 100%;
        border-radius: 12px 0 0 12px;
    }
    .metric-card.blue::before  { background: #58A6FF; }
    .metric-card.green::before { background: #3FB950; }
    .metric-card.orange::before{ background: #F78166; }
    .metric-card.purple::before{ background: #BC8CFF; }

    .metric-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8B949E;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #E6EDF3;
        line-height: 1;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #8B949E;
        margin-top: 0.35rem;
    }
    .metric-delta-pos { color: #3FB950; font-weight: 600; }
    .metric-delta-neg { color: #F78166; font-weight: 600; }

    /* Section headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        color: #E6EDF3;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.2rem;
    }
    .section-sub {
        font-size: 0.8rem;
        color: #8B949E;
        margin-bottom: 1rem;
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #161B22 0%, #0D1117 60%);
        border: 1px solid #21262D;
        border-radius: 14px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.7rem;
        font-weight: 700;
        color: #E6EDF3;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 0.875rem;
        color: #8B949E;
        margin-top: 0.4rem;
    }
    .hero-badge {
        background: #21262D;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 0.2rem 0.6rem;
        font-size: 0.72rem;
        color: #58A6FF;
        font-weight: 600;
        display: inline-block;
        margin-top: 0.6rem;
        letter-spacing: 0.05em;
    }

    /* Dividers */
    hr { border-color: #21262D; margin: 1.5rem 0; }

    /* Plotly chart backgrounds */
    .js-plotly-plot .plotly .main-svg { border-radius: 10px; }

    /* Remove default Streamlit metric styling */
    [data-testid="metric-container"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── Data Generation ─────────────────────────────────────────────────────────
@st.cache_data
def generate_data(n_athletes=50, n_days=60, seed=42):
    np.random.seed(seed)
    records = []
    start_date = datetime(2024, 1, 1)

    for athlete_id in range(1, n_athletes + 1):
        # Per-athlete baselines (natural variation between athletes)
        base_sleep       = np.random.normal(7.0, 0.8)
        base_meditation  = np.random.normal(20, 8)
        base_performance = np.random.normal(65, 10)
        stress_sensitivity = np.random.uniform(0.6, 1.4)  # how reactive to poor habits

        for day in range(n_days):
            date = start_date + timedelta(days=day)
            week = day // 7

            # Weekly progression: athletes generally improve over 60 days
            trend = week * 0.15

            # Daily sleep with autocorrelation (bad sleep clusters)
            sleep_noise = np.random.normal(0, 0.5)
            sleep_hours = np.clip(base_sleep + sleep_noise + trend * 0.05, 4.0, 10.0)

            # Meditation: slight positive trend, high variance day to day
            med_noise = np.random.normal(0, 5)
            meditation_min = np.clip(base_meditation + med_noise + trend * 0.4, 0, 60)

            # Stress: driven DOWN by sleep and meditation (with noise)
            stress_driver = (
                - 0.35 * (sleep_hours - 7)        # more sleep → less stress
                - 0.08 * (meditation_min - 20)     # more meditation → less stress
                + np.random.normal(0, 1.0)
            ) * stress_sensitivity
            stress = np.clip(5.5 + stress_driver - trend * 0.03, 1, 10)

            # Performance: driven UP by sleep, meditation, and LOW stress
            perf_driver = (
                  2.5  * (sleep_hours - 7)          # sleep boosts performance
                + 0.30 * (meditation_min - 20)       # meditation boosts performance
                - 2.0  * (stress - 5)                # stress hurts performance
                + np.random.normal(0, 4)
            )
            performance = np.clip(base_performance + perf_driver + trend * 0.4, 10, 100)

            records.append({
                "Athlete_ID"               : f"ATH-{athlete_id:03d}",
                "Date"                     : date,
                "Sleep_Hours"              : round(float(sleep_hours), 2),
                "Meditation_Minutes"       : round(float(meditation_min), 1),
                "Self_Reported_Stress"     : round(float(stress), 2),
                "Training_Performance_Score": round(float(performance), 1),
            })

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
    return df

df = generate_data()

# ─── Sidebar Filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    st.markdown("---")

    all_athletes = sorted(df["Athlete_ID"].unique())
    athlete_options = ["All Athletes"] + all_athletes
    selected_athletes = st.multiselect(
        "Select Athletes",
        options=all_athletes,
        default=[],
        placeholder="All athletes shown",
    )

    st.markdown("")
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    st.markdown("---")
    st.markdown("## 📊 Chart Options")
    show_rolling = st.checkbox("Show 7-day rolling average", value=True)
    scatter_x    = st.selectbox(
        "Scatter X-axis",
        ["Self_Reported_Stress", "Sleep_Hours", "Meditation_Minutes"],
        index=0,
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.72rem;color:#8B949E;line-height:1.6;'>"
        "Dataset: 50 athletes · 60 days<br>"
        "Synthetic data with realistic<br>psychophysiological correlations."
        "</div>",
        unsafe_allow_html=True,
    )

# ─── Apply Filters ───────────────────────────────────────────────────────────
filtered = df.copy()

if selected_athletes:
    filtered = filtered[filtered["Athlete_ID"].isin(selected_athletes)]

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered = filtered[
        (filtered["Date"].dt.date >= start_d) &
        (filtered["Date"].dt.date <= end_d)
    ]

# ─── Hero Banner ─────────────────────────────────────────────────────────────
athlete_label = (
    f"{len(selected_athletes)} athlete{'s' if len(selected_athletes) != 1 else ''}"
    if selected_athletes else "All 50 athletes"
)
days_shown = filtered["Date"].nunique()

st.markdown(f"""
<div class="hero">
  <div style="font-size:3rem;line-height:1;">🧘</div>
  <div>
    <div class="hero-title">Athlete Mindfulness &amp; Performance Tracker</div>
    <div class="hero-subtitle">
      Explore how sleep, meditation, and stress shape athletic output over time.
    </div>
    <span class="hero-badge">
      {athlete_label} &nbsp;·&nbsp; {days_shown} days selected
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── KPI Cards ───────────────────────────────────────────────────────────────
avg_meditation  = filtered["Meditation_Minutes"].mean()
avg_performance = filtered["Training_Performance_Score"].mean()
avg_sleep       = filtered["Sleep_Hours"].mean()
avg_stress      = filtered["Self_Reported_Stress"].mean()

# Compare to global averages for delta
global_avg_med  = df["Meditation_Minutes"].mean()
global_avg_perf = df["Training_Performance_Score"].mean()
global_avg_slp  = df["Sleep_Hours"].mean()
global_avg_str  = df["Self_Reported_Stress"].mean()

def delta_html(val, baseline, invert=False):
    diff = val - baseline
    positive_is_good = not invert
    sign = "+" if diff >= 0 else ""
    cls = "metric-delta-pos" if (diff >= 0) == positive_is_good else "metric-delta-neg"
    return f'<span class="{cls}">{sign}{diff:.1f} vs avg</span>'

c1, c2, c3, c4 = st.columns(4)

cards = [
    (c1, "blue",   "⏱️", "Avg Meditation",  f"{avg_meditation:.1f} min",  delta_html(avg_meditation, global_avg_med),    "per session"),
    (c2, "green",  "🏅", "Avg Performance", f"{avg_performance:.1f}",     delta_html(avg_performance, global_avg_perf),  "out of 100"),
    (c3, "purple", "💤", "Avg Sleep",       f"{avg_sleep:.1f} hrs",       delta_html(avg_sleep, global_avg_slp),         "per night"),
    (c4, "orange", "🧠", "Avg Stress",      f"{avg_stress:.1f} / 10",     delta_html(avg_stress, global_avg_str, invert=True), "self-reported"),
]
for col, color, icon, label, value, delta, sub in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card {color}">
          <div class="metric-label">{icon} {label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-sub">{delta} &nbsp;·&nbsp; {sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Line Chart: Meditation + Performance Over Time ──────────────────────────
st.markdown("""
<div class="section-header">📈 Trends Over Time</div>
<div class="section-sub">Daily averages across selected athletes — meditation minutes and performance scores</div>
""", unsafe_allow_html=True)

daily = (
    filtered.groupby("Date")
    .agg(
        Meditation_Minutes        =("Meditation_Minutes", "mean"),
        Training_Performance_Score=("Training_Performance_Score", "mean"),
        Sleep_Hours               =("Sleep_Hours", "mean"),
    )
    .reset_index()
    .sort_values("Date")
)

if show_rolling:
    daily["Med_Roll7"]  = daily["Meditation_Minutes"].rolling(7, min_periods=1).mean()
    daily["Perf_Roll7"] = daily["Training_Performance_Score"].rolling(7, min_periods=1).mean()

PLOT_BG     = "#0D1117"
PAPER_BG    = "#0D1117"
GRID_COLOR  = "#21262D"
FONT_COLOR  = "#8B949E"
BLUE        = "#58A6FF"
GREEN       = "#3FB950"
ORANGE      = "#F78166"
PURPLE      = "#BC8CFF"

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

# Raw daily lines (faint)
fig_trend.add_trace(
    go.Scatter(
        x=daily["Date"], y=daily["Meditation_Minutes"],
        name="Meditation (daily avg)", mode="lines",
        line=dict(color=PURPLE, width=1.2, dash="dot"),
        opacity=0.4,
    ), secondary_y=False,
)
fig_trend.add_trace(
    go.Scatter(
        x=daily["Date"], y=daily["Training_Performance_Score"],
        name="Performance (daily avg)", mode="lines",
        line=dict(color=BLUE, width=1.2, dash="dot"),
        opacity=0.4,
    ), secondary_y=True,
)

if show_rolling:
    fig_trend.add_trace(
        go.Scatter(
            x=daily["Date"], y=daily["Med_Roll7"],
            name="Meditation (7-day avg)", mode="lines",
            line=dict(color=PURPLE, width=2.5),
        ), secondary_y=False,
    )
    fig_trend.add_trace(
        go.Scatter(
            x=daily["Date"], y=daily["Perf_Roll7"],
            name="Performance (7-day avg)", mode="lines",
            line=dict(color=BLUE, width=2.5),
        ), secondary_y=True,
    )

fig_trend.update_layout(
    height=380,
    paper_bgcolor=PAPER_BG,
    plot_bgcolor=PLOT_BG,
    font=dict(color=FONT_COLOR, family="Inter"),
    legend=dict(
        bgcolor="#161B22", bordercolor="#21262D", borderwidth=1,
        font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
    ),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified",
)
fig_trend.update_xaxes(
    gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, showline=False, tickfont=dict(size=11),
)
fig_trend.update_yaxes(
    gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, showline=False, tickfont=dict(size=11),
    title_text="<b>Meditation</b> (minutes)", title_font=dict(color=PURPLE, size=11), secondary_y=False,
)
fig_trend.update_yaxes(
    gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, showline=False, tickfont=dict(size=11),
    title_text="<b>Performance</b> (score)", title_font=dict(color=BLUE, size=11), secondary_y=True,
)

st.plotly_chart(fig_trend, use_container_width=True)

# ─── Bottom Row: Scatter + Heatmap ───────────────────────────────────────────
st.markdown("---")
col_left, col_right = st.columns([1.1, 1], gap="large")

# ── Scatter: Stress vs Performance ──
with col_left:
    axis_label_map = {
        "Self_Reported_Stress"     : "Stress Level (1–10)",
        "Sleep_Hours"              : "Sleep Hours",
        "Meditation_Minutes"       : "Meditation Minutes",
    }
    st.markdown(f"""
    <div class="section-header">🔍 Relationship Explorer</div>
    <div class="section-sub">{axis_label_map[scatter_x]} vs Training Performance Score</div>
    """, unsafe_allow_html=True)

    sample = filtered.sample(min(len(filtered), 800), random_state=1)

    fig_scatter = px.scatter(
        sample,
        x=scatter_x,
        y="Training_Performance_Score",
        color="Sleep_Hours",
        color_continuous_scale=[[0, "#161B22"], [0.3, PURPLE], [0.6, BLUE], [1.0, GREEN]],
        opacity=0.65,
        trendline="ols",
        labels={
            scatter_x                     : axis_label_map[scatter_x],
            "Training_Performance_Score"  : "Performance Score",
            "Sleep_Hours"                 : "Sleep (hrs)",
        },
        hover_data={"Athlete_ID": True, "Date": True},
    )
    fig_scatter.update_traces(
        marker=dict(size=5),
        selector=dict(mode="markers"),
    )
    fig_scatter.update_traces(
        line=dict(color=ORANGE, width=2.5, dash="dash"),
        selector=dict(type="scatter", mode="lines"),
    )
    fig_scatter.update_layout(
        height=380,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR, family="Inter"),
        coloraxis_colorbar=dict(
            title="Sleep<br>(hrs)",
            tickfont=dict(size=10),
            thickness=12, len=0.7,
        ),
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ── Correlation Heatmap ──
with col_right:
    st.markdown("""
    <div class="section-header">📐 Correlation Matrix</div>
    <div class="section-sub">Pearson r between all tracked metrics</div>
    """, unsafe_allow_html=True)

    corr_cols = [
        "Sleep_Hours", "Meditation_Minutes",
        "Self_Reported_Stress", "Training_Performance_Score",
    ]
    corr_labels = ["Sleep\nHours", "Meditation\nMins", "Stress\nLevel", "Performance\nScore"]
    corr_matrix = filtered[corr_cols].corr()

    # Build annotated text
    text_vals = [[f"{corr_matrix.iloc[i, j]:.2f}" for j in range(4)] for i in range(4)]

    fig_heat = go.Figure(go.Heatmap(
        z=corr_matrix.values,
        x=corr_labels,
        y=corr_labels,
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=13, color="white", family="Space Grotesk"),
        colorscale=[
            [0.0,  "#F78166"],
            [0.5,  "#161B22"],
            [1.0,  "#3FB950"],
        ],
        zmin=-1, zmax=1,
        showscale=True,
        colorbar=dict(
            title="r", tickfont=dict(size=10),
            thickness=12, len=0.7,
        ),
    ))
    fig_heat.update_layout(
        height=380,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR, family="Inter", size=11),
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(side="bottom"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ─── Weekly Trends Table ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="section-header">📅 Weekly Averages</div>
<div class="section-sub">Aggregated performance and mindfulness metrics by ISO week</div>
""", unsafe_allow_html=True)

weekly = (
    filtered.groupby("Week")
    .agg(
        Avg_Sleep        =("Sleep_Hours", "mean"),
        Avg_Meditation   =("Meditation_Minutes", "mean"),
        Avg_Stress       =("Self_Reported_Stress", "mean"),
        Avg_Performance  =("Training_Performance_Score", "mean"),
        Athletes_Tracked =("Athlete_ID", "nunique"),
    )
    .reset_index()
    .rename(columns={
        "Week"            : "ISO Week",
        "Avg_Sleep"       : "Sleep (hrs)",
        "Avg_Meditation"  : "Meditation (min)",
        "Avg_Stress"      : "Stress (1–10)",
        "Avg_Performance" : "Performance",
        "Athletes_Tracked": "Athletes",
    })
)
weekly = weekly.round(2)

st.dataframe(
    weekly.style
    .format({
        "Sleep (hrs)"      : "{:.2f}",
        "Meditation (min)" : "{:.1f}",
        "Stress (1–10)"    : "{:.2f}",
        "Performance"      : "{:.1f}",
    })
    .background_gradient(subset=["Performance"],    cmap="Greens")
    .background_gradient(subset=["Stress (1–10)"],  cmap="Reds_r")
    .background_gradient(subset=["Meditation (min)"], cmap="Purples"),
    use_container_width=True,
    hide_index=True,
    height=310,
)

# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown("""
<hr>
<div style="text-align:center; font-size:0.75rem; color:#484F58; padding-bottom:1rem;">
  Athlete Mindfulness &amp; Performance Tracker &nbsp;·&nbsp;
  Synthetic dataset — 50 athletes, 60 days &nbsp;·&nbsp;
  Built with Streamlit &amp; Plotly
</div>
""", unsafe_allow_html=True)