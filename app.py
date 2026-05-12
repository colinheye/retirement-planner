import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import retirement_planner as m

st.set_page_config(page_title="Retirement Planner", layout="wide", initial_sidebar_state="expanded")
st.title("Monte Carlo Retirement Planner")

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Configuration")

    with st.expander("Timeline", expanded=True):
        c1, c2 = st.columns(2)
        start_year  = int(c1.number_input("Start Year",       value=2027, step=1))
        start_age   = int(c2.number_input("Current Age",      value=39,   step=1))
        ret_age     = int(c1.number_input("Retirement Age",   value=65,   step=1))
        sim_count   = int(c2.number_input("Simulations",      value=5000, step=1000, min_value=500))
        min_buffer  = float(st.number_input("Min Liquid Buffer ($)", value=300_000, step=50_000))

    with st.expander("Accounts"):
        brok_bal   = float(st.number_input("Brokerage Balance",    value=1_650_000, step=50_000))
        brok_basis = float(st.number_input("Brokerage Cost Basis", value=500_000,   step=50_000))
        hsa_bal    = float(st.number_input("HSA Balance",          value=70_000,    step=5_000))
        ira_bal    = float(st.number_input("IRA Balance",          value=100_000,   step=5_000))
        trad_bal   = float(st.number_input("Traditional 401k",     value=400_000,   step=10_000))
        roth_bal   = float(st.number_input("Roth 401k",            value=400_000,   step=10_000))

    with st.expander("Income"):
        init_income      = float(st.number_input("Your Income (today's $)", value=150_000, step=5_000))
        c1, c2 = st.columns(2)
        rg_mean = float(c1.number_input("Real Growth Mean", value=0.015, step=0.005, format="%.3f"))
        rg_std  = float(c2.number_input("Real Growth Std",  value=0.040, step=0.005, format="%.3f"))
        income_floor = float(st.slider("Income Floor (% of start)", 0.30, 1.00, 0.60, 0.05))

    with st.expander("Social Security"):
        ss_start   = int(st.number_input("SS Start Age",     value=65,     step=1))
        ss_primary = float(st.number_input("Primary Benefit",value=48_000, step=1_000))
        ss_spouse  = float(st.number_input("Spouse Benefit", value=24_000, step=1_000))
        ss_haircut = st.slider("Benefit Received (%)", 50, 100, 75, 5) / 100.0

    with st.expander("Spouse"):
        spouse_income = float(st.number_input("Spouse Income", value=180_000, step=5_000))
        spouse_works  = st.checkbox("Spouse Works", value=False)
        if spouse_works:
            _stop = int(st.number_input("Stop Year (0 = until retirement)", value=0, step=1))
            spouse_stop = None if _stop == 0 else _stop
        else:
            spouse_stop = start_year  # never works (yr < start_year is always False)

    with st.expander("Children"):
        children_raw = st.text_input("Birth Years (comma-separated)", value="")
        try:
            children_birth_years = [int(y.strip()) for y in children_raw.split(",") if y.strip()]
        except ValueError:
            children_birth_years = []
            st.warning("Invalid birth years — using none")

    with st.expander("Expenses"):
        living_exp = float(st.number_input("Base Living Expenses", value=100_000, step=5_000))
        ltc_active = st.checkbox("LTC Event Active", value=True)
        c1, c2 = st.columns(2)
        ltc_age  = int(c1.number_input("LTC Start Age",   value=95,      step=1))
        ltc_cost = float(c2.number_input("LTC Annual Cost", value=120_000, step=10_000))

    with st.expander("Home"):
        home_val    = float(st.number_input("Current Value",      value=1_200_000, step=50_000))
        home_mort   = float(st.number_input("Mortgage Balance",   value=950_000,   step=50_000))
        home_yrs    = int(st.number_input("Mortgage Years Left",  value=29,        step=1))
        home_apprec = float(st.slider("Appreciation Rate", 0.00, 0.08, 0.03, 0.005, format="%.3f"))
        st.caption("Move/Upgrade Event")
        sell_yr      = int(st.number_input("Sell Year (years elapsed)", value=5, step=1))
        new_home_val = float(st.number_input("New Home Value (today's $)", value=1_500_000, step=50_000))
        new_mort_rt  = float(st.slider("New Mortgage Rate", 0.03, 0.10, 0.065, 0.0025, format="%.4f"))

    with st.expander("Windfalls"):
        gift_amt  = float(st.number_input("Annual Gift",          value=75_000,    step=5_000))
        gift_yrs  = int(st.number_input("Gift Years Remaining",   value=1,         step=1))
        inh_amt   = float(st.number_input("Inheritance Amount",   value=1_000_000, step=100_000))
        inh_year  = int(st.number_input("Expected Year",          value=2045,      step=1))
        inh_prob  = float(st.slider("Probability (%)", 0, 100, 10, 5)) / 100.0

    with st.expander("Market & Inflation"):
        c1, c2 = st.columns(2)
        infl_mean = float(c1.slider("Inflation Mean",    0.00, 0.08, 0.030, 0.005, format="%.3f"))
        infl_std  = float(c2.slider("Inflation Std",     0.00, 0.05, 0.015, 0.005, format="%.3f"))
        stk_mean  = float(c1.slider("Stock Mean",        0.00, 0.15, 0.080, 0.005, format="%.3f"))
        stk_std   = float(c2.slider("Stock Std",         0.00, 0.30, 0.160, 0.005, format="%.3f"))
        bnd_mean  = float(c1.slider("Bond Mean",         0.00, 0.10, 0.040, 0.005, format="%.3f"))
        bnd_std   = float(c2.slider("Bond Std",          0.00, 0.15, 0.050, 0.005, format="%.3f"))

    with st.expander("Guardrails"):
        gr_active = st.checkbox("Active", value=True)
        c1, c2 = st.columns(2)
        gr_lower = float(c1.number_input("Lower ($)", value=1_000_000, step=100_000))
        gr_upper = float(c2.number_input("Upper ($)", value=6_000_000, step=500_000))
        gr_cut   = float(c1.slider("Spend Cut",  0.00, 0.30, 0.10, 0.01))
        gr_raise = float(c2.slider("Spend Raise",0.00, 0.20, 0.05, 0.01))

    with st.expander("Roth Conversion"):
        roth_active  = st.checkbox("Active", value=True, key="roth_active")
        roth_bracket = float(st.selectbox("Target Bracket Top",
                             [0.10, 0.12, 0.22, 0.24, 0.32], index=2,
                             format_func=lambda x: f"{x:.0%}"))
        roth_max = float(st.number_input("Annual Max ($)", value=100_000, step=10_000))

    with st.expander("Longevity"):
        c1, c2 = st.columns(2)
        p_mean  = int(c1.number_input("Primary Mean",  value=90,  step=1))
        p_std   = int(c2.number_input("Primary Std",   value=9,   step=1))
        s_mean  = int(c1.number_input("Spouse Mean",   value=93,  step=1))
        s_std   = int(c2.number_input("Spouse Std",    value=9,   step=1))
        lon_min = int(c1.number_input("Min Age",       value=72,  step=1))
        lon_max = int(c2.number_input("Max Age",       value=115, step=1))

    run_btn = st.button("Run Simulation", type="primary", use_container_width=True)

# ── Config application ────────────────────────────────────────────────────────

def apply_config():
    m.START_YEAR        = start_year
    m.START_AGE         = start_age
    m.RETIREMENT_AGE    = ret_age
    m.SIMULATION_COUNT  = sim_count
    m.MIN_LIQUID_BUFFER = min_buffer

    m.ACCOUNTS = {
        'cash_brokerage': {'balance': brok_bal, 'basis': brok_basis},
        'hsa':       hsa_bal,
        'ira':       ira_bal,
        'trad_401k': trad_bal,
        'roth_401k': roth_bal,
    }

    m.INITIAL_INCOME = init_income
    m.SOC_SEC = {
        'start_age':       ss_start,
        'benefit_primary': ss_primary,
        'benefit_spouse':  ss_spouse,
        'haircut':         ss_haircut,
    }
    m.BASE_LIVING_EXPENSES = living_exp

    m.RATES.update({
        'inflation_mean':        infl_mean,
        'inflation_std':         infl_std,
        'stock_mean':            stk_mean,
        'stock_std':             stk_std,
        'bond_mean':             bnd_mean,
        'bond_std':              bnd_std,
        'home_appreciation':     home_apprec,
        'real_income_growth_mean': rg_mean,
        'real_income_growth_std':  rg_std,
        'real_income_floor':       income_floor,
    })

    m.CURRENT_HOME = {'value': home_val, 'mortgage': home_mort, 'years': home_yrs}
    m.HOUSE_EVENT.update({
        'sell_year':      sell_yr,
        'new_home_value': new_home_val,
        'mortgage_rate':  new_mort_rt,
    })

    m.LTC_EVENT = {'active': ltc_active, 'age_start': ltc_age, 'annual_cost': ltc_cost}

    m.ANNUAL_GIFT  = {'amount': gift_amt, 'years_remaining': gift_yrs}
    m.INHERITANCE  = {'amount': inh_amt, 'expected_year': inh_year, 'probability': inh_prob}

    m.CHILDREN_BIRTH_YEARS = children_birth_years
    m.SPOUSE = {'income': spouse_income, 'stop_year': spouse_stop}

    m.GUARDRAILS.update({
        'active':          gr_active,
        'lower_threshold': gr_lower,
        'upper_threshold': gr_upper,
        'spend_cut':       gr_cut,
        'spend_raise':     gr_raise,
    })
    m.ROTH_CONVERSION = {
        'active':             roth_active,
        'target_bracket_top': roth_bracket,
        'annual_max':         roth_max,
    }
    m.LONGEVITY = {
        'primary_mean': p_mean, 'primary_std': p_std,
        'spouse_mean':  s_mean, 'spouse_std':  s_std,
        'min_age':      lon_min, 'max_age':    lon_max,
    }

# ── Simulation runner ─────────────────────────────────────────────────────────

def run_simulation():
    apply_config()
    n = sim_count
    fails, fail_years, all_dfs, final_nw = 0, [], [], []

    progress = st.progress(0.0, text=f"Running {n:,} simulations…")
    for i in range(n):
        model = m.FinancialModel(i)
        f, fy, df = model.run()
        if f:
            fails += 1
            if fy:
                fail_years.append(fy)
        all_dfs.append(df)
        final_nw.append((i, float(df.iloc[-1]['Liquid_Assets'])))
        if i % max(1, n // 100) == 0:
            progress.progress(i / n, text=f"Running simulations… {i:,} / {n:,}")
    progress.empty()

    combined = pd.concat(all_dfs, ignore_index=True)
    success_rate  = 100.0 * (1 - fails / n)
    median_legacy = combined.groupby('Run')['Liquid_Assets'].last().median()
    avg_fail_age  = (np.mean(fail_years) - start_year + start_age) if fail_years else None

    final_nw.sort(key=lambda x: x[1])
    p25_run = final_nw[n // 4][0]
    p25_df  = combined[combined['Run'] == p25_run].copy()

    return {
        'combined':     combined,
        'p25_df':       p25_df,
        'success_rate': success_rate,
        'median_legacy': median_legacy,
        'avg_fail_age': avg_fail_age,
        'fail_count':   fails,
        'n':            n,
    }

# ── Trigger ───────────────────────────────────────────────────────────────────

if run_btn:
    with st.spinner(""):
        st.session_state['results'] = run_simulation()

# ── Results ───────────────────────────────────────────────────────────────────

if 'results' not in st.session_state:
    st.info("Configure parameters in the sidebar, then click **Run Simulation**.")
    st.stop()

r        = st.session_state['results']
combined = r['combined']
p25_df   = r['p25_df']

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Success Rate",    f"{r['success_rate']:.1f}%")
col2.metric("Median Legacy",   f"${r['median_legacy']:,.0f}")
col3.metric("Failures",        f"{r['fail_count']:,} / {r['n']:,}")
col4.metric("Avg Insolvency Age",
            f"{r['avg_fail_age']:.1f}" if r['avg_fail_age'] else "N/A")

st.divider()

# ── Chart 1: Liquid Asset Runway ──────────────────────────────────────────────

stats = (combined.groupby('Age')['Liquid_Assets']
         .quantile([0.10, 0.25, 0.50, 0.75, 0.90])
         .unstack())
ages = stats.index.tolist()

fig1 = go.Figure()
fig1.add_hrect(
    y0=0, y1=min_buffer,
    fillcolor="red", opacity=0.12, line_width=0,
    annotation_text="Insolvency Zone", annotation_position="top left",
)
fig1.add_trace(go.Scatter(
    x=ages, y=stats[0.75], line=dict(width=0), showlegend=False, name="75th",
))
fig1.add_trace(go.Scatter(
    x=ages, y=stats[0.25], fill="tonexty",
    fillcolor="rgba(30,100,255,0.12)", line=dict(width=0), name="25th–75th Band",
))
fig1.add_trace(go.Scatter(
    x=ages, y=stats[0.50], line=dict(color="blue", width=2), name="Median (50th)",
))
fig1.add_trace(go.Scatter(
    x=ages, y=stats[0.25],
    line=dict(color="orange", width=1.5, dash="dash"), name="25th Percentile",
))
fig1.add_trace(go.Scatter(
    x=ages, y=stats[0.10],
    line=dict(color="red", width=1.5, dash="dot"), name="10th Percentile",
))
fig1.update_layout(
    title="Liquid Asset Runway (All Accounts, No Home Equity)",
    xaxis_title="Age", yaxis_title="Liquid Assets ($)",
    yaxis_tickformat="$,.0f", hovermode="x unified",
    legend=dict(orientation="h", y=-0.18),
)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: 25th Percentile Account Balances ─────────────────────────────────

ACCT_COLS   = ["Brokerage", "HSA", "IRA", "Trad_401k", "Roth_401k"]
ACCT_LABELS = ["Brokerage", "HSA", "IRA", "Trad 401k", "Roth 401k"]
ACCT_COLORS = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd"]

fig2 = go.Figure()
for col, label, color in zip(ACCT_COLS, ACCT_LABELS, ACCT_COLORS):
    fig2.add_trace(go.Scatter(
        x=p25_df["Year"], y=p25_df[col],
        name=label, stackgroup="one",
        line=dict(color=color, width=0.5),
        fillcolor=color + "cc",
        mode="lines",
    ))
fig2.update_layout(
    title="25th Percentile Run: Account Balances",
    xaxis_title="Year", yaxis_title="Balance ($)",
    yaxis_tickformat="$,.0f", hovermode="x unified",
    legend=dict(orientation="h", y=-0.18),
)
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: 25th Percentile Cash Flow ───────────────────────────────────────

EXP_COLS   = ["Exp_Living", "Exp_Home", "Exp_Kids", "Exp_Health", "Exp_Car", "Exp_Repair"]
EXP_LABELS = ["Living", "Mortgage", "Kids/College", "Health/LTC", "Cars", "Home Repair"]
EXP_COLORS = ["#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#aec7e8"]

fig3 = go.Figure()
for col, label, color in zip(EXP_COLS, EXP_LABELS, EXP_COLORS):
    fig3.add_trace(go.Scatter(
        x=p25_df["Year"], y=p25_df[col],
        name=label, stackgroup="one",
        line=dict(color=color, width=0.5),
        fillcolor=color + "cc",
        mode="lines",
    ))
fig3.add_trace(go.Scatter(
    x=p25_df["Year"],
    y=p25_df["Wage_Income"] + p25_df["SS_Income"],
    name="Total Income (Wage + SS)",
    line=dict(color="black", width=2.5, dash="dash"),
    mode="lines",
))
fig3.update_layout(
    title="25th Percentile Run: Cash Flow",
    xaxis_title="Year", yaxis_title="Annual Amount ($)",
    yaxis_tickformat="$,.0f", hovermode="x unified",
    legend=dict(orientation="h", y=-0.18),
)
st.plotly_chart(fig3, use_container_width=True)
