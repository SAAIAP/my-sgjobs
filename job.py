import streamlit as st
import pandas as pd
import ast
import altair as alt

# Page config must be first Streamlit command
st.set_page_config(page_title="Singapore Job Dashboard", layout="wide")

DATA_PATH = "./data/SGJobData.csv.gz"
REQUIRED_COLUMNS = [
    "categories",
    "employmentTypes",
    "positionLevels",
    "status_jobStatus",
    "average_salary",
    "salary_minimum",
    "salary_maximum",
    "minimumYearsExperience",
    "metadata_totalNumberOfView",
    "metadata_totalNumberJobApplication",
    "metadata_newPostingDate",
    "metadata_originalPostingDate",
    "numberOfVacancies",
    "postedCompany_name",
    "title",
]

@st.cache_data
def load_data(path):
    return pd.read_csv(path)


def validate_required_columns(dataframe):
    return [col for col in REQUIRED_COLUMNS if col not in dataframe.columns]


# Page title
st.header("Team 1")
st.title("Singapore Job Prospect Dashboard")
st.caption("NTU STCP | One North | Live Classroom")

st.markdown("""
- This dashboard shows Singapore job posting data
- Filters are available from the sidebar
- KPI cards and table update based on selected filters
-* strong column for reporting*
-title
-postedCompany_name
-category_names
-employmentTypes
-positionLevels
-minimumYearsExperience
-numberOfVacancies
-average_salary
-metadata_totalNumberOfView
-metadata_totalNumberJobApplication
-metadata_newPostingDate
-status_jobStatus            
-SGJobData.csv contains job postings data with various attributes such as category, employment type, position level, salary, and more.            
""")

try:
    df = load_data(DATA_PATH)
except Exception as exc:
    st.error(f"Unable to load dataset: {exc}")
    st.stop()

missing_columns = validate_required_columns(df)
if missing_columns:
    st.error("The uploaded dataset is missing required columns. Please include the following columns:")
    st.write(", ".join(REQUIRED_COLUMNS)
    )
    st.write("Missing columns:", ", ".join(missing_columns))
    st.stop()

# Convert date column
df["metadata_newPostingDate"] = pd.to_datetime(
    df["metadata_newPostingDate"],
    errors="coerce"
)

# Extract category names
def extract_category_names(value):
    try:
        categories = ast.literal_eval(value)
        return ", ".join([item.get("category", "") for item in categories])
    except Exception:
        return ""

df["category_names"] = df["categories"].apply(extract_category_names)

# Sidebar filters
st.sidebar.header("Filters")

# Category options from split categories
category_options = sorted(
    df["category_names"]
    .dropna()
    .str.split(", ")
    .explode()
    .unique()
)

selected_categories = st.sidebar.multiselect(
    "Category",
    category_options
)

employment_options = sorted(df["employmentTypes"].dropna().unique())

selected_employment = st.sidebar.multiselect(
    "Employment Type",
    employment_options
)

position_options = sorted(df["positionLevels"].dropna().unique())

selected_positions = st.sidebar.multiselect(
    "Position Level",
    position_options
)

status_options = sorted(df["status_jobStatus"].dropna().unique())

selected_status = st.sidebar.multiselect(
    "Job Status",
    status_options
)

min_salary = int(df["average_salary"].min())
max_salary = int(df["average_salary"].max())

salary_range = st.sidebar.slider(
    "Average Salary Range",
    min_value=min_salary,
    max_value=max_salary,
    value=(min_salary, max_salary)
)

min_exp = int(df["minimumYearsExperience"].min())
max_exp = int(df["minimumYearsExperience"].max())

experience_range = st.sidebar.slider(
    "Minimum Years Experience",
    min_value=min_exp,
    max_value=max_exp,
    value=(min_exp, max_exp)
)

# Apply filters
filtered_df = df.copy()

if selected_categories:
    filtered_df = filtered_df[
        filtered_df["category_names"].apply(
            lambda x: any(category in x for category in selected_categories)
        )
    ]

if selected_employment:
    filtered_df = filtered_df[
        filtered_df["employmentTypes"].isin(selected_employment)
    ]

if selected_positions:
    filtered_df = filtered_df[
        filtered_df["positionLevels"].isin(selected_positions)
    ]

if selected_status:
    filtered_df = filtered_df[
        filtered_df["status_jobStatus"].isin(selected_status)
    ]

filtered_df = filtered_df[
    (filtered_df["average_salary"] >= salary_range[0]) &
    (filtered_df["average_salary"] <= salary_range[1])
]

filtered_df = filtered_df[
    (filtered_df["minimumYearsExperience"] >= experience_range[0]) &
    (filtered_df["minimumYearsExperience"] <= experience_range[1])
]

# KPI row based on filtered data
st.header("Dashboard Overview")

total_jobs = len(filtered_df)
avg_salary = filtered_df["average_salary"].mean()
min_salary_avg = filtered_df["salary_minimum"].mean()
max_salary_avg = filtered_df["salary_maximum"].mean()
total_views = filtered_df["metadata_totalNumberOfView"].sum()
total_applications = filtered_df["metadata_totalNumberJobApplication"].sum()
total_vacancies = filtered_df["numberOfVacancies"].sum()

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

col1.metric("Total Jobs", f"{total_jobs:,}")
col2.metric("Avg Salary", f"${avg_salary:,.0f}")
col3.metric("Avg Min Salary", f"${min_salary_avg:,.0f}")
col4.metric("Avg Max Salary", f"${max_salary_avg:,.0f}")
col5.metric("Total Views", f"{total_views:,}")
col6.metric("Applications", f"{total_applications:,}")
col7.metric("Vacancies", f"{total_vacancies:,}")

st.divider()

# Prepare display table
cols = ["category_names"] + [
    col for col in filtered_df.columns
    if col not in ["categories", "category_names"]
]

display_df = filtered_df[cols]

st.write(f"Filtered Rows: {len(filtered_df):,} | Columns: {len(display_df.columns)}")

# Display only once
st.dataframe(
    display_df.head(1000),
    use_container_width=True
)

# lets perform some salary analysis based on the filtered data
st.divider()

st.header("Salary Analysis")

for col in ["salary_minimum", "salary_maximum", "average_salary", "minimumYearsExperience"]:
    filtered_df[col] = pd.to_numeric(filtered_df[col], errors="coerce")

tab1, tab2, tab3, tab4 = st.tabs([
    "By Category",
    "By Position Level",
    "By Employment Type",
    "By Experience"
])

with tab1:
    st.subheader("Average Salary by Job Category")

    category_salary_df = filtered_df.copy()
    category_salary_df["single_category"] = (
        category_salary_df["category_names"]
        .fillna("")
        .str.split(", ")
    )
    category_salary_df = category_salary_df.explode("single_category")

    category_salary = (
        category_salary_df
        .groupby("single_category")
        .agg(
            avg_salary=("average_salary", "mean"),
            min_salary=("salary_minimum", "min"),
            max_salary=("salary_maximum", "max"),
            job_count=("title", "count")
        )
        .sort_values("avg_salary", ascending=False)
        .reset_index()
    )

    st.dataframe(category_salary, use_container_width=True)
    st.bar_chart(category_salary.head(15), x="single_category", y="avg_salary")

with tab2:
    st.subheader("Average Salary by Position Level")

    salary_by_position = (
        filtered_df
        .groupby("positionLevels")
        .agg(
            avg_salary=("average_salary", "mean"),
            min_salary=("salary_minimum", "min"),
            max_salary=("salary_maximum", "max"),
            job_count=("title", "count")
        )
        .sort_values("avg_salary", ascending=False)
        .reset_index()
    )

    st.dataframe(salary_by_position, use_container_width=True)
    st.bar_chart(salary_by_position, x="positionLevels", y="avg_salary")

with tab3:
    st.subheader("Average Salary by Employment Type")

    salary_by_employment = (
        filtered_df
        .groupby("employmentTypes")
        .agg(
            avg_salary=("average_salary", "mean"),
            min_salary=("salary_minimum", "min"),
            max_salary=("salary_maximum", "max"),
            job_count=("title", "count")
        )
        .sort_values("avg_salary", ascending=False)
        .reset_index()
    )

    st.dataframe(salary_by_employment, use_container_width=True)
    st.bar_chart(salary_by_employment, x="employmentTypes", y="avg_salary")

with tab4:
    st.subheader("Average Salary by Years of Experience")

    salary_by_experience = (
        filtered_df
        .groupby("minimumYearsExperience")
        .agg(
            avg_salary=("average_salary", "mean"),
            min_salary=("salary_minimum", "min"),
            max_salary=("salary_maximum", "max"),
            job_count=("title", "count")
        )
        .sort_values("minimumYearsExperience")
        .reset_index()
    )

    st.dataframe(salary_by_experience, use_container_width=True)
    st.line_chart(salary_by_experience, x="minimumYearsExperience", y="avg_salary")


    st.divider()

    # Job analysis by experience
    # =========================
# Salary Analysis
# =========================

# =========================
# Job Market Trends
# =========================

st.header("Job Market Trends")

# Clean required columns
filtered_df["metadata_newPostingDate"] = pd.to_datetime(
    filtered_df["metadata_newPostingDate"],
    errors="coerce"
)

filtered_df["metadata_originalPostingDate"] = pd.to_datetime(
    filtered_df["metadata_originalPostingDate"],
    errors="coerce"
)

filtered_df["numberOfVacancies"] = pd.to_numeric(
    filtered_df["numberOfVacancies"],
    errors="coerce"
)

# KPI row for Job Market Trends
companies_hiring = filtered_df["postedCompany_name"].nunique()
avg_vacancies = filtered_df["numberOfVacancies"].mean()
total_vacancies = filtered_df["numberOfVacancies"].sum()

job_categories = (
    filtered_df["category_names"]
    .dropna()
    .str.split(", ")
    .explode()
    .nunique()
)

trend_col1, trend_col2, trend_col3, trend_col4 = st.columns(4)

trend_col1.metric("Companies Hiring", f"{companies_hiring:,}")
trend_col2.metric("Job Categories", f"{job_categories:,}")
trend_col3.metric("Avg Vacancies / Listing", f"{avg_vacancies:,.1f}")
trend_col4.metric("Total Vacancies", f"{total_vacancies:,.0f}")

st.divider()

# Tabs
market_tab1, market_tab2, market_tab3, market_tab4 = st.tabs([
    "Top Companies",
    "Demand by Category",
    "Posting Trend",
    "Vacancies"
])

# =========================
# Tab 1: Top Companies
# =========================

with market_tab1:
    st.subheader("Which companies post the most jobs?")

    top_companies = (
        filtered_df["postedCompany_name"]
        .dropna()
        .value_counts()
        .head(15)
        .reset_index()
    )

    top_companies.columns = ["Company", "Job Count"]

    company_chart = (
        alt.Chart(top_companies)
        .mark_bar()
        .encode(
            x=alt.X("Job Count:Q", title="Number of Job Postings"),
            y=alt.Y("Company:N", sort="-x", title="Company"),
            tooltip=[
                alt.Tooltip("Company:N", title="Company"),
                alt.Tooltip("Job Count:Q", title="Job Count")
            ]
        )
        .properties(height=500)
    )

    st.altair_chart(company_chart, width='stretch')
    st.dataframe(top_companies, use_container_width=True)

# =========================
# Tab 2: Demand by Category
# =========================

with market_tab2:
    st.subheader("Which job categories are most in demand?")

    category_df = filtered_df.copy()

    category_df["single_category"] = (
        category_df["category_names"]
        .fillna("")
        .str.split(", ")
    )

    category_df = category_df.explode("single_category")

    category_demand = (
        category_df["single_category"]
        .dropna()
        .value_counts()
        .head(15)
        .reset_index()
    )

    category_demand.columns = ["Category", "Job Count"]

    category_chart = (
        alt.Chart(category_demand)
        .mark_bar()
        .encode(
            x=alt.X("Job Count:Q", title="Number of Job Postings"),
            y=alt.Y("Category:N", sort="-x", title="Job Category"),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Job Count:Q", title="Job Count")
            ]
        )
        .properties(height=500)
    )

    st.altair_chart(category_chart, width='stretch')
    st.dataframe(category_demand, use_container_width=True)

# =========================
# Tab 3: Posting Trend
# =========================

with market_tab3:
    st.subheader("How has job posting volume changed over time?")

    new_posting_trend = (
        filtered_df
        .dropna(subset=["metadata_newPostingDate"])
        .groupby("metadata_newPostingDate")
        .size()
        .reset_index(name="Job Count")
    )

    new_posting_trend["Date Type"] = "New Posting Date"

    new_posting_trend = new_posting_trend.rename(
        columns={"metadata_newPostingDate": "Posting Date"}
    )

    original_posting_trend = (
        filtered_df
        .dropna(subset=["metadata_originalPostingDate"])
        .groupby("metadata_originalPostingDate")
        .size()
        .reset_index(name="Job Count")
    )

    original_posting_trend["Date Type"] = "Original Posting Date"

    original_posting_trend = original_posting_trend.rename(
        columns={"metadata_originalPostingDate": "Posting Date"}
    )

    posting_trend = pd.concat(
        [new_posting_trend, original_posting_trend],
        ignore_index=True
    )

    posting_chart = (
        alt.Chart(posting_trend)
        .mark_line(point=True)
        .encode(
            x=alt.X("Posting Date:T", title="Posting Date"),
            y=alt.Y("Job Count:Q", title="Number of Job Postings"),
            color=alt.Color("Date Type:N", title="Date Type"),
            tooltip=[
                alt.Tooltip("Posting Date:T", title="Posting Date"),
                alt.Tooltip("Job Count:Q", title="Job Count"),
                alt.Tooltip("Date Type:N", title="Date Type")
            ]
        )
        .properties(height=450)
    )

    st.altair_chart(posting_chart, width='stretch')
    st.dataframe(posting_trend, use_container_width=True)

# =========================
# Tab 4: Vacancies
# =========================

with market_tab4:
    st.subheader("What is the average number of vacancies per listing?")

    vacancy_df = filtered_df.copy()

    vacancy_df["single_category"] = (
        vacancy_df["category_names"]
        .fillna("")
        .str.split(", ")
    )

    vacancy_df = vacancy_df.explode("single_category")

    vacancy_by_category = (
        vacancy_df
        .dropna(subset=["single_category"])
        .groupby("single_category")
        .agg(
            avg_vacancies=("numberOfVacancies", "mean"),
            total_vacancies=("numberOfVacancies", "sum"),
            job_count=("title", "count")
        )
        .sort_values("avg_vacancies", ascending=False)
        .reset_index()
        .head(15)
    )

    vacancy_by_category.columns = [
        "Category",
        "Average Vacancies",
        "Total Vacancies",
        "Job Count"
    ]

    vacancy_chart = (
        alt.Chart(vacancy_by_category)
        .mark_bar()
        .encode(
            x=alt.X(
                "Average Vacancies:Q",
                title="Average Vacancies per Listing"
            ),
            y=alt.Y(
                "Category:N",
                sort="-x",
                title="Job Category"
            ),
            tooltip=[
                alt.Tooltip("Category:N", title="Category"),
                alt.Tooltip("Average Vacancies:Q", title="Average Vacancies", format=".1f"),
                alt.Tooltip("Total Vacancies:Q", title="Total Vacancies", format=",.0f"),
                alt.Tooltip("Job Count:Q", title="Job Count")
            ]
        )
        .properties(height=500)
    )

    st.altair_chart(vacancy_chart, width='stretch')
    st.dataframe(vacancy_by_category, use_container_width=True)