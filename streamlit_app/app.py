import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

from database import RedshiftClient
from queries import get_incidents_query


st.set_page_config(
    page_title="ServicePulse",
    page_icon="📊",
    layout="wide",
)

# Custom CSS for professional look
st.markdown(
    """
    <style>
    .kpi-card {
        background-color: #f8f9fa;
        border-left: 4px solid #0066cc;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .kpi-value {
        font-size: 32px;
        font-weight: bold;
        color: #0066cc;
    }
    .kpi-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🚨 ServicePulse")
st.subheader("Enterprise Ticket Intelligence Dashboard")
st.caption("Real-time ticket analytics powered by AWS Redshift")

# Data freshness indicator
col_refresh, col_status = st.columns([1, 3])
with col_refresh:
    last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.metric(
        "🟢 Data Status",
        "Connected",
    )
with col_status:
    st.write(
        f"**Last refreshed:** {last_refresh}  "
        f"| **Source:** AWS Redshift Serverless"
    )


@st.cache_data(ttl=300)
def load_incidents():
    client = RedshiftClient()
    return client.execute_query(get_incidents_query())


def calculate_incident_age_days(created_at):
    """Calculate incident age in days"""
    if pd.isna(created_at):
        return None
    created = pd.to_datetime(created_at)
    return (datetime.now() - created).days


try:
    with st.spinner("Loading incident data..."):
        df = load_incidents()

    # Convert created_at to datetime
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["updated_at"] = pd.to_datetime(df["updated_at"])

    # ========== SIDEBAR FILTERS ==========
    st.sidebar.title("📋 Filters")

    # Date range filter
    min_date = df["created_at"].min().date()
    max_date = df["created_at"].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[
            (df["created_at"].dt.date >= start_date)
            & (df["created_at"].dt.date <= end_date)
        ]

    # State filter
    st.sidebar.subheader("State")
    all_states = st.sidebar.checkbox(
        "All States",
        value=True,
        key="state_all",
    )
    if all_states:
        selected_states = df["state_label"].unique().tolist()
    else:
        selected_states = st.sidebar.multiselect(
            "Select States",
            df["state_label"].unique(),
            default=df["state_label"].unique().tolist(),
        )
    df = df[df["state_label"].isin(selected_states)]

    # Priority filter
    st.sidebar.subheader("Priority")
    all_priorities = st.sidebar.checkbox(
        "All Priorities",
        value=True,
        key="priority_all",
    )
    if all_priorities:
        selected_priorities = df[
            "priority_label"
        ].unique().tolist()
    else:
        selected_priorities = st.sidebar.multiselect(
            "Select Priorities",
            df["priority_label"].unique(),
            default=df["priority_label"].unique().tolist(),
        )
    df = df[df["priority_label"].isin(selected_priorities)]

    # Category filter
    st.sidebar.subheader("Category")
    all_categories = st.sidebar.checkbox(
        "All Categories",
        value=True,
        key="category_all",
    )
    if all_categories:
        selected_categories = df["category"].unique().tolist()
    else:
        selected_categories = st.sidebar.multiselect(
            "Select Categories",
            df["category"].unique(),
            default=df["category"].unique().tolist(),
        )
    df = df[df["category"].isin(selected_categories)]

    # ========== KPI CARDS ==========
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)

    # Total Incidents
    with col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{len(df)}</div>
                <div class="kpi-label">Total Incidents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Open Incidents
    with col2:
        open_count = len(
            df[df["state_label"] != "Closed"]
        )
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{open_count}</div>
                <div class="kpi-label">Open Incidents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Critical Open Incidents
    with col3:
        critical_open_count = len(
            df[
                (df["priority_label"] == "Critical")
                & (df["state_label"] != "Closed")
            ]
        )
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{critical_open_count}</div>
                <div class="kpi-label">Critical Open</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Average Incident Age
    with col4:
        avg_age = df["incident_age_days"].mean()
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{avg_age:.1f}</div>
                <div class="kpi-label">Avg Age (days)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # On Hold
    with col5:
        on_hold_count = len(
            df[df["state_label"] == "On Hold"]
        )
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{on_hold_count}</div>
                <div class="kpi-label">On Hold</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ========== CHARTS ROW 1 ==========
    col1, col2 = st.columns(2)

    with col1:
        # Incident Trend (Monthly Aggregation)
        df_trend = df.copy()
        df_trend["year_month"] = df_trend[
            "created_at"
        ].dt.to_period("M")
        monthly_incidents = (
            df_trend.groupby("year_month")
            .size()
            .reset_index(name="count")
        )
        monthly_incidents["year_month"] = monthly_incidents[
            "year_month"
        ].astype(str)
        monthly_incidents.columns = [
            "month",
            "incidents",
        ]

        trend_chart = px.line(
            monthly_incidents,
            x="month",
            y="incidents",
            title="📈 Incident Trend (Monthly)",
            markers=True,
            template="plotly_white",
            labels={
                "month": "Month",
                "incidents": "Incident Count",
            },
        )
        trend_chart.update_traces(
            line=dict(color="#0066cc", width=3),
            marker=dict(size=8),
        )
        st.plotly_chart(
            trend_chart,
            use_container_width=True,
        )

    with col2:
        # Incident Status Distribution
        state_dist = (
            df["state_label"].value_counts().reset_index()
        )
        state_dist.columns = ["state", "count"]

        status_chart = px.pie(
            state_dist,
            values="count",
            names="state",
            title="🔴 Incident Status Distribution",
            template="plotly_white",
        )
        status_chart.update_traces(
            textposition="inside",
            textinfo="percent+label",
        )
        st.plotly_chart(
            status_chart,
            use_container_width=True,
        )

    # ========== CHARTS ROW 2 ==========
    col1, col2 = st.columns(2)

    with col1:
        # Priority Distribution
        priority_dist = (
            df["priority_label"]
            .value_counts()
            .reset_index()
        )
        priority_dist.columns = ["priority", "count"]

        # Define priority order
        priority_order = [
            "Critical",
            "High",
            "Moderate",
            "Low",
            "Planning",
        ]
        priority_dist["priority"] = pd.Categorical(
            priority_dist["priority"],
            categories=priority_order,
            ordered=True,
        )
        priority_dist = priority_dist.sort_values(
            "priority",
            ascending=False,
        )

        priority_chart = px.bar(
            priority_dist,
            x="count",
            y="priority",
            orientation="h",
            title="⚠️ Priority Distribution",
            template="plotly_white",
            labels={
                "count": "Number of Incidents",
                "priority": "Priority",
            },
        )
        priority_chart.update_traces(
            marker=dict(
                color=[
                    "#d32f2f",
                    "#f57c00",
                    "#fbc02d",
                    "#388e3c",
                    "#1976d2",
                ][:len(priority_dist)]
            )
        )
        st.plotly_chart(
            priority_chart,
            use_container_width=True,
        )

    with col2:
        # Category Distribution
        category_dist = (
            df["category"].value_counts().reset_index()
        )
        category_dist.columns = ["category", "count"]

        category_chart = px.bar(
            category_dist,
            x="count",
            y="category",
            orientation="h",
            title="📂 Category Distribution",
            template="plotly_white",
            labels={
                "count": "Number of Incidents",
                "category": "Category",
            },
        )
        category_chart.update_traces(
            marker=dict(color="#0066cc")
        )
        st.plotly_chart(
            category_chart,
            use_container_width=True,
        )

    # ========== CHARTS ROW 3 ==========
    # Incident Aging Analysis
    aging_buckets = pd.cut(
        df["incident_age_days"],
        bins=[0, 2, 7, 14, 30, float("inf")],
        labels=[
            "0-2 days",
            "3-7 days",
            "8-14 days",
            "15-30 days",
            "30+ days",
        ],
        right=True,
    )
    aging_dist = aging_buckets.value_counts().reset_index()
    aging_dist.columns = ["age_bucket", "count"]

    # Reorder buckets
    bucket_order = [
        "0-2 days",
        "3-7 days",
        "8-14 days",
        "15-30 days",
        "30+ days",
    ]
    aging_dist["age_bucket"] = pd.Categorical(
        aging_dist["age_bucket"],
        categories=bucket_order,
        ordered=True,
    )
    aging_dist = aging_dist.sort_values("age_bucket")

    aging_chart = px.bar(
        aging_dist,
        x="age_bucket",
        y="count",
        title="⏱️ Incident Aging Analysis",
        template="plotly_white",
        labels={
            "age_bucket": "Age Bucket",
            "count": "Number of Incidents",
        },
    )
    aging_chart.update_traces(marker=dict(color="#ff6b6b"))
    st.plotly_chart(
        aging_chart,
        use_container_width=True,
    )

    st.markdown("---")

    # ========== INCIDENT DETAILS TABLE ==========
    st.subheader("📋 Incident Details")

    # Display columns
    display_cols = [
        "incident_number",
        "short_description",
        "state_label",
        "priority_label",
        "category",
        "urgency",
        "impact",
        "incident_age_days",
        "created_at",
    ]

    # Prepare dataframe for display
    df_display = df[display_cols].copy()
    df_display.columns = [
        "ID",
        "Description",
        "State",
        "Priority",
        "Category",
        "Urgency",
        "Impact",
        "Age (days)",
        "Created",
    ]
    df_display["Created"] = df_display["Created"].dt.strftime(
        "%Y-%m-%d %H:%M"
    )

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )

except Exception as exc:
    st.error(f"Unable to load Redshift data: {exc}")