"""
Streamlit Barebone Starter -- Week 9
========================================
Clone this repo, then run:
    uv run streamlit run src/week9_streamlit_starter.py

This is intentionally minimal. In class we will build it up together:
    - add sidebar filters
    - add KPI metrics
    - add a drilldown chart with a dimension/metric picker
    - publish it to Streamlit Community Cloud

Data source: processed_data_cube.csv, produced by running main.py
(the cube is created by create_cubes() in stage_3_aggregate.py).
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Home Credit Dashboard", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data"/  "processed_data_cube.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


def main():
    st.title("Home Credit Dashboard-today is 10/02 hi everyone")
    st.markdown("Starter dashboard -- we'll build this up together in class.")

    df = load_data()

    month_min = int(df["MONTH_APPLIED"].min())
    month_max = int(df["MONTH_APPLIED"].max())
    month_from, month_to = st.slider(
        "Application month range",
        min_value=month_min,
        max_value=month_max,
        value=(month_min, month_max),
        step=1,
    )

    filtered_df = df[df["MONTH_APPLIED"].between(month_from, month_to)].copy()

    total_applications = float(filtered_df["total_applications"].sum())
    total_defaults = float(filtered_df["total_defaults"].sum())
    total_credit = float(filtered_df["total_credit"].sum())
    default_rate = (total_defaults / total_applications * 100) if total_applications else 0.0

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("Total Applications", f"{total_applications / 1000:,.1f}K")
    metric_col_2.metric("Default Rate", f"{default_rate:.2f}%")
    metric_col_3.metric("Total Credit", f"${total_credit / 1_000_000:,.1f}M")

    group_options = {
        "NAME_CONTRACT_TYPE": "Loan type",
        "AGE_GROUP": "Age group",
        "HOME_CAR_OWNERSHIP": "Home/Car ownership",
        "AGE_GENDER_SEGMENT": "Age-gender segment",
        "CREDIT_INCOME_RATIO_GROUP": "Credit-income ratio group",
        "YEARS_EMPLOYED_GROUP": "Years employed group",
        "BURDEN_CAT": "Burden category",
    }
    metric_options = {
        "total_applications": "Application count",
        "default_rate": "Default rate",
        "total_credit": "Total credit amount",
    }

    st.sidebar.subheader("Drilldown controls")
    dimension_choice = st.sidebar.selectbox(
        "Group by",
        options=list(group_options.keys()),
        format_func=lambda option: group_options[option],
    )
    metric_choice = st.sidebar.selectbox(
        "Metric",
        options=list(metric_options.keys()),
        format_func=lambda option: metric_options[option],
    )

    grouped_df = (
        filtered_df.groupby(dimension_choice, dropna=False)
        .agg(
            application_count=("total_applications", "sum"),
            default_count=("total_defaults", "sum"),
            total_credit=("total_credit", "sum"),
        )
        .reset_index()
    )

    if metric_choice == "default_rate":
        grouped_df["metric_value"] = (
            grouped_df["default_count"] / grouped_df["application_count"] * 100
        ).replace([float("inf"), -float("inf")], 0.0).fillna(0.0)
        metric_label = "Default rate (%)"
    elif metric_choice == "total_credit":
        grouped_df["metric_value"] = grouped_df["total_credit"].fillna(0.0)
        metric_label = "Total credit amount"
    else:
        grouped_df["metric_value"] = grouped_df["application_count"].fillna(0.0)
        metric_label = "Application count"

    grouped_df = grouped_df.rename(columns={dimension_choice: "dimension_value"})
    grouped_df = grouped_df.sort_values("metric_value", ascending=False)

    fig = px.bar(
        grouped_df,
        x="dimension_value",
        y="metric_value",
        title=f"{metric_label} by {group_options[dimension_choice]}",
        labels={"dimension_value": group_options[dimension_choice], "metric_value": metric_label},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Detail by {group_options[dimension_choice]}")
    summary_df = grouped_df[["dimension_value", "application_count", "default_count"]].copy()
    summary_df = summary_df.rename(
        columns={
            "dimension_value": group_options[dimension_choice],
            "application_count": "Application count",
            "default_count": "Default count",
        }
    )
    st.dataframe(summary_df, use_container_width=True)

    st.subheader("Monthly business and default trend")
    monthly_df = (
        filtered_df
        .groupby("MONTH_APPLIED", as_index=False)
        .agg(
            application_count=("total_applications", "sum"),
            default_count=("total_defaults", "sum"),
            total_credit=("total_credit", "sum"),
        )
        .copy()
    )
    monthly_df["default_rate"] = (
        monthly_df["default_count"] / monthly_df["application_count"] * 100
    ).replace([float("inf"), -float("inf")], 0.0).fillna(0.0)

    monthly_bar = px.bar(
        monthly_df,
        x="MONTH_APPLIED",
        y="application_count",
        title="Monthly application count",
        labels={"MONTH_APPLIED": "Application month", "application_count": "Application count"},
    )
    st.plotly_chart(monthly_bar, use_container_width=True)

    monthly_line = px.line(
        monthly_df,
        x="MONTH_APPLIED",
        y="default_rate",
        title="Monthly default rate",
        markers=True,
        labels={"MONTH_APPLIED": "Application month", "default_rate": "Default rate (%)"},
    )
    st.plotly_chart(monthly_line, use_container_width=True)

    st.subheader("Data cube preview")
    st.dataframe(filtered_df.head(20), width='stretch')


if __name__ == "__main__":
    main()
