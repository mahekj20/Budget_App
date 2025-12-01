# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from streamlit_option_menu import option_menu

# ------------------- Page Config -------------------
st.set_page_config(
    page_title="India Union Budget Explorer 2014–2025",
    page_icon="India",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Made by a Data Science Student\nVisualizing India's changing priorities"
    }
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main {background-color: #0e1117; color: #fafafa;}
    .stPlotlyChart {background-color: #1e1e1e; border-radius: 12px; padding: 10px;}
    .css-1d391kg {padding-top: 1rem;}
    .metric-card {
        background-color: #1e293b; padding: 1.5rem; border-radius: 12px; text-align: center;
        border: 1px solid #334155;
    }
    .title-font {font-size: 3.2rem !important; font-weight: 700; background: linear-gradient(90deg, #ff8c00, #ffc107, #28a745); 
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .subtitle {font-size: 1.3rem; color: #94a3b8;}
</style>
""", unsafe_allow_html=True)

# ------------------- Load & Clean Data -------------------
@st.cache_data
def load_data():
    df = pd.read_csv("budget.csv")
    
    # Standardize ministry names
    df["Ministry"] = df["Ministry Name"].replace({
        "MINISTRY OF AGRICULTURE": "Agriculture & Farmers' Welfare",
        "MINISTRY OF AGRICULTURE AND FARMERS WELFARE": "Agriculture & Farmers' Welfare",
        "MINISTRY OF AGRICULTURE AND FARMERS' WELFARE": "Agriculture & Farmers' Welfare",
        "MINISTRY OF DEFENCE": "Defence",
        "MINISTRY OF FINANCE": "Finance",
        "MINISTRY OF HOME AFFAIRS": "Home Affairs",
        "MINISTRY OF HEALTH AND FAMILY WELFARE": "Health & Family Welfare"
    }).str.replace("MINISTRY OF ", "", regex=False)
    
    # Clean numeric columns
    cols = ['Revenue (Plan)', 'Capital (Plan)', 'Total (Plan)',
            'Revenue (Non-Plan)', 'Capital (Non-Plan)', 'Total (Non-Plan)', 'Total Plan & Non-Plan']
    for col in cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    df["Total"] = df["Total Plan & Non-Plan"].fillna(df["Total (Plan)"])
    df["Year"] = df["Year"].str[:9]
    
    return df

df = load_data()
focus_ministries = ["Defence", "Finance", "Home Affairs", "Agriculture & Farmers' Welfare", "Health & Family Welfare"]
df = df[df["Ministry"].isin(focus_ministries)]

# Total budget per year
total_by_year = df.groupby("Year")["Total"].sum().reset_index()
df = df.merge(total_by_year, on="Year", suffixes=('', '_total'))
df["Share (%)"] = (df["Total"] / df["Total_total"]) * 100

# Indian Rupee formatter
def format_inr(x):
    if x >= 1e7:  # > 1 lakh crore
        return f"₹{x/1e7:.2f} Lakh Cr"
    elif x >= 1e5:
        return f"₹{x/1e5:.1f} Thousand Cr"
    else:
        return f"₹{x:,.0f} Cr"

# ------------------- Sidebar -------------------
with st.sidebar:
    st.image("https://flagcdn.com/in.png", width=80)
    st.title("India Budget Explorer")
    st.markdown("**2014 – 2025** | Union Budget Trends")
    
    selected = option_menu(
        menu_title=None,
        options=["Overview", "Deep Dive", "Comparisons", "What If?"],
        icons=["house", "bar-chart", "graph-up", "sliders"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#1e293b"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#0d6efd"},
        }
    )

    year = st.selectbox("Select Year", sorted(df["Year"].unique(), reverse=True))
    ministry = st.selectbox("Ministry", focus_ministries)

# ------------------- Main Dashboard -------------------
if selected == "Overview":
    st.markdown("<h1 class='title-font'>India's Budget Priorities</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>How national spending has dramatically shifted in a decade</p>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    latest = df[df["Year"] == "2024-2025"]
    defence = latest[latest["Ministry"] == "Defence"]["Total"].iloc[0]
    finance = latest[latest["Ministry"] == "Finance"]["Total"].iloc[0]
    agri_share_2014 = df[(df["Year"] == "2014-2015") & (df["Ministry"] == "Agriculture & Farmers' Welfare")]["Share (%)"].iloc[0]
    agri_share_2024 = df[(df["Year"] == "2024-2025") & (df["Ministry"] == "Agriculture & Farmers' Welfare")]["Share (%)"].iloc[0]

    with col1:
        st.markdown(f"<div class='metric-card'><h3>{defence/1e7:.1f} Lakh Cr</h3><p>Defence 2024-25</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h3>{finance/1e7:.1f} Lakh Cr</h3><p>Finance (Interest + Grants)</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>{(defence/1e7):.0f} Lakh Cr</h3><p>9.4× growth since 2014</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><h3>{agri_share_2014:.1f}% → {agri_share_2024:.1f}%</h3><p>Agriculture Share</p></div>", unsafe_allow_html=True)

    # Animated Treemap
    st.markdown("### Budget Distribution Over Time")
    fig = px.treemap(
        df, path=['Year', 'Ministry'], values='Total',
        color='Share (%)', hover_data={'Total': ':,.0f'},
        color_continuous_scale="RdYlBu_r",
        title="Interactive Budget Hierarchy (Hover + Click to Explore)"
    )
    fig.update_layout(margin=dict(t=50, l=0, r=0, b=0), height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Share Trend
    st.markdown("### Who Gets What? (% Share of Total Budget)")
    fig2 = px.area(df, x="Year", y="Share (%)", color="Ministry",
                   color_discrete_sequence=px.colors.qualitative.Set2,
                   title="Decline of Development, Rise of Security & Debt")
    fig2.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig2, use_container_width=True)

elif selected == "Deep Dive":
    st.markdown(f"### Deep Dive: {ministry}")
    data = df[df["Ministry"] == ministry]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(data, x="Year", y="Total", title="Total Allocation (₹ Crore)",
                     color_discrete_sequence=["#0d6efd"])
        fig.update_yaxes(title="₹ Crore")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(data, x="Year", y="Share (%)", markers=True,
                      title="% Share of Total Budget", color_discrete_sequence=["#dc3545"])
        fig.add_hline(y=data["Share (%)"].mean(), line_dash="dot", annotation_text="Average Share")
        st.plotly_chart(fig, use_container_width=True)

    # CAGR
    first = data.iloc[0]["Total"]
    last = data.iloc[-1]["Total"]
    years = len(data) - 1
    cagr = ((last / first) ** (1/years) - 1) * 100
    st.success(f"**CAGR (2014–2025):** {cagr:+.2f}% per year")

elif selected == "Comparisons":
    st.markdown("### Cross-Ministry Comparisons")

    metric = st.radio("Compare by", ["Absolute Amount", "Growth Rate", "% Share"], horizontal=True)

    if metric == "Absolute Amount":
        fig = px.bar(df[df["Year"] == year], x="Ministry", y="Total", title=f"Budget {year}")
        st.plotly_chart(fig, use_container_width=True)

    elif metric == "% Share":
        fig = px.pie(df[df["Year"] == year], values="Total", names="Ministry",
                     title=f"Budget Composition {year}", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    else:
        growth = df.pivot(index="Ministry", columns="Year", values="Total")
        growth_pct = growth.pct_change(axis=1) * 100
        latest_growth = growth_pct["2024-2025"]
        fig = px.bar(x=latest_growth.index, y=latest_growth.values, title="YoY Growth 2024-25")
        st.plotly_chart(fig, use_container_width=True)

    st.info("Finance Ministry includes interest payments on debt — now larger than Defence!")

elif selected == "What If?":
    st.markdown("### What If India Reallocated Its Budget?")
    total_2024 = df[df["Year"] == "2024-2025"]["Total_total"].iloc[0] / 1e7  # Lakh Cr

    st.markdown(f"#### Total Budget 2024-25: **₹{total_2024:.1f} Lakh Crore**")
    st.markdown("Drag to reallocate (total must stay same)")

    allocations = {}
    for m in focus_ministries:
        current = df[(df["Year"] == "2024-2025") & (df["Ministry"] == m)]["Total"].iloc[0] / 1e7
        allocations[m] = st.slider(m, 0.0, total_2024, current, 0.5)

    total_allocated = sum(allocations.values())
    st.write(f"**Allocated:** ₹{total_allocated:.1f} Lakh Cr | **Remaining:** ₹{total_2024 - total_allocated:.1f} Lakh Cr")

    if abs(total_allocated - total_2024) < 5:
        fig = px.pie(names=allocations.keys(), values=allocations.values(), title="Your Budget")
        st.plotly_chart(fig, use_container_width=True)
        st.balloons()
        st.success("Balanced budget! Well done!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b;'>
    Made with ❤️ by a Data Science Student | Data Source: Union Budget of India (2014–2025)<br>
    <a href='https://github.com/yourusername/india-budget-explorer'>GitHub</a> • 
    Deployed on <a href='https://share.streamlit.io'>Streamlit Community Cloud</a>
</div>
""", unsafe_allow_html=True)
