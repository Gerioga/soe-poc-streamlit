"""
SOE Proof of Concept Dashboard — Serbia, Poland, Romania, Montenegro
Fiscal-risk oriented redesign.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os

st.set_page_config(page_title="SOE Fiscal Risk — 4-country POC", layout="wide", initial_sidebar_state="collapsed")

# ================ AUTH ================
PASSWORD = "Arlington"
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("## SOE Fiscal Risk — Serbia, Poland, Romania, Montenegro")
    pw = st.text_input("Password", type="password")
    if st.button("Enter"):
        if pw == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Wrong password")
    st.stop()

# ================ LOAD DATA ================
BASE = os.path.dirname(os.path.abspath(__file__))

# mtime-keyed loaders so Streamlit Cloud's @st.cache_data rebuilds when the
# JSON files are updated on redeploy (caught a stale 2-country cache on 2026-04-16).
def _mtime(name):
    p = os.path.join(BASE, name)
    return os.path.getmtime(p) if os.path.exists(p) else 0

@st.cache_data
def load_financial(_mt):
    with open(os.path.join(BASE, 'financial.json'), 'r', encoding='utf-8') as f:
        return pd.DataFrame(json.load(f))

@st.cache_data
def load_emissions(_mt):
    with open(os.path.join(BASE, 'emissions.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_analytics(_mt):
    with open(os.path.join(BASE, 'analytics.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

df = load_financial(_mtime('financial.json'))
em = load_emissions(_mtime('emissions.json'))
an = load_analytics(_mtime('analytics.json'))
em_df = pd.DataFrame(em['companies'])
soe_df = pd.DataFrame(an['soes'])

SRB_COLOR = '#c8102e'
POL_COLOR = '#005288'
ROU_COLOR = '#ffd200'
MNE_COLOR = '#7b3294'
COUNTRY_COLOR = {'Serbia': SRB_COLOR, 'Poland': POL_COLOR, 'Romania': ROU_COLOR, 'Montenegro': MNE_COLOR}
COUNTRIES = ['Serbia', 'Poland', 'Romania', 'Montenegro']
QUAD_COLOR = {
    'Fiscal risk':          '#d62728',
    'Strategic asset':      '#2ca02c',
    'Small & loss-making':  '#ff7f0e',
    'Small & performing':   '#1f77b4',
    'Insufficient data':    '#bbbbbb',
}
TRANS_COLOR = {
    'Transition liability':     '#d62728',
    'Transition opportunity':   '#2ca02c',
    'Low transition exposure':  '#7fc97f',
    'Mixed':                    '#ffbf00',
    'Not covered':              '#bbbbbb',
}
DIR_ICON = {'deteriorating': '🔻', 'improving': '🔺', 'stable': '➡️', 'insufficient data': '…'}

# ================ DEFINITIONS HELPER ================
def definition(text):
    """Investopedia-style short read-this caption rendered below a chart/table."""
    st.markdown(
        f'<div style="font-size:12px; color:#64748b; background:#f8fafc; '
        f'border-left:3px solid #94a3b8; padding:6px 10px; margin:4px 0 18px 0;">'
        f'<b>How to read:</b> {text}</div>',
        unsafe_allow_html=True)

# ================ HEADER ================
st.markdown("""
<style>
.big-title {font-size:28px; font-weight:700; margin-bottom:0;}
.subtitle  {color:#64748b; font-size:14px; margin-top:0;}
.stTabs [data-baseweb="tab"] {padding: 8px 18px; font-size:14px;}
div[data-testid="stMetricValue"] {font-size:22px !important;}
.risk-high {background:#fde2e2; padding:2px 8px; border-radius:4px; display:inline-block; font-size:12px;}
.risk-mid  {background:#fff4d6; padding:2px 8px; border-radius:4px; display:inline-block; font-size:12px;}
.risk-low  {background:#e3f4e3; padding:2px 8px; border-radius:4px; display:inline-block; font-size:12px;}
.kpi-card  {border:1px solid #e5e7eb; border-radius:6px; padding:14px; background:#fafbfc;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">SOE Fiscal Risk Lens — Serbia · Poland · Romania · Montenegro</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Where state-owned enterprises sit on the fiscal-risk and transition-risk map. Proof of concept.</p>', unsafe_allow_html=True)

# ================ TABS ================
tabs = st.tabs(["Executive", "Country Benchmark", "Transition", "Trends", "Deep Dive", "Data Table", "About"])

countries = an['country_aggregates']

# ============================================================
# TAB 1 — EXECUTIVE
# ============================================================
with tabs[0]:
    st.markdown("### Executive summary")
    st.caption("One view of the SOE portfolio's size, performance, leverage and transition exposure in each country.")

    # ---- KPI rows per country (stacked full-width so labels don't truncate)
    def kpi_card(c):
        a = countries.get(c)
        if not a:
            st.markdown(f"#### {c}")
            st.info(f"Aggregate data for {c} is still loading. Refresh the page in a few seconds.")
            return
        st.markdown(f"#### {c}")
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("SOEs", a['n_soes'])
        k2.metric("Combined revenue", f"${a['agg_revenue_usd']/1000:,.1f}B")
        k3.metric("Portfolio ROA", f"{a['agg_roa']:.2f}%" if a['agg_roa'] is not None else "—",
                  help="Asset-weighted: Σ(Net profit) ÷ Σ(Total assets)")
        k4.metric("Top-3 concentration", f"{a['top3_revenue_share']:.0f}%" if a['top3_revenue_share'] else "—",
                  help="Share of SOE revenue captured by the three largest")
        k5,k6,k7,k8 = st.columns(4)
        k5.metric("Combined assets", f"${a['agg_assets_usd']/1000:,.1f}B")
        k6.metric("Combined debt", f"${a['agg_debt_usd']/1000:,.1f}B" if a['agg_debt_usd'] else "—")
        k7.metric("Fiscal-risk SOEs", a['n_fiscal_risk'],
                  help="Large SOEs (above median revenue) with negative ROA")
        emi_t = a.get('agg_emissions_t') or 0
        k8.metric("Scope 1 emissions", f"{emi_t/1e6:.1f} MtCO₂e" if emi_t else "—",
                  help="Scope 1 matched only for Serbia & Poland in this POC")

    for c in COUNTRIES:
        kpi_card(c)
        st.markdown("")

    st.markdown("---")

    # ---- Quadrant scatter
    st.markdown("#### Portfolio map — Size × Return on assets")
    st.caption("Each bubble = one SOE (bubble = revenue). The red quadrant (large + loss-making) is where explicit fiscal risk concentrates.")

    scat = soe_df.dropna(subset=['revenue_usd', 'roa']).copy()
    # compute median revenue for quadrant lines (all SOEs, both countries)
    rev_med = scat['revenue_usd'].median()

    fig = px.scatter(
        scat, x='revenue_usd', y='roa',
        color='quadrant', color_discrete_map=QUAD_COLOR,
        size='revenue_usd', size_max=45,
        hover_name='company',
        custom_data=['country','risk_score','quadrant','roa_direction','revenue_usd'],
        log_x=True,
        labels={'revenue_usd':'Revenue (USD mn, log)','roa':'ROA (%)'},
    )
    fig.update_traces(hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "Country: %{customdata[0]}<br>"
        "Revenue: $%{customdata[4]:,.0f} mn<br>"
        "ROA: %{y:.1f}%<br>"
        "Quadrant: %{customdata[2]}<br>"
        "ROA trend: %{customdata[3]}<br>"
        "Risk score: %{customdata[1]}<extra></extra>"
    ))
    fig.add_hline(y=0, line_dash='dot', line_color='#888', opacity=0.5,
                  annotation_text="ROA = 0", annotation_position="bottom right")
    fig.add_vline(x=rev_med, line_dash='dot', line_color='#888', opacity=0.5,
                  annotation_text=f"Median revenue ${rev_med:,.0f} mn", annotation_position="top right")
    fig.update_layout(height=520, legend_title_text='Quadrant',
                      margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True)
    definition(
        "X = revenue (log scale); Y = Return on Assets (ROA = Net Profit ÷ Total Assets, Investopedia). "
        "The vertical line is the portfolio-median revenue; the horizontal line is ROA = 0. "
        "Bubbles in the top-right are large AND profitable (strategic assets); the bottom-right "
        "(large + loss-making, in red) is where fiscal risk concentrates.")

    q_counts = scat['quadrant'].value_counts().to_dict()
    st.markdown(
        " &nbsp;&nbsp; ".join([f"<b>{k}:</b> {v}" for k,v in q_counts.items()]),
        unsafe_allow_html=True)

    st.markdown("---")

    # ---- Top risk table
    st.markdown("#### Top risk list")
    st.caption("Weighted risk score combines size (35%), profitability (30%), leverage (15%) and emissions intensity (20%). Higher = more attention warranted. See *About* for the full formula.")

    top = pd.DataFrame(an['top_risks']).head(10)
    top['Risk'] = top['risk_score'].apply(lambda v: '🔴 High' if v>=70 else ('🟡 Medium' if v>=40 else '🟢 Low'))
    top['Trend'] = top['roa_direction'].map(DIR_ICON).fillna('…')
    top['Revenue (USDm)'] = top['revenue_usd'].round(0)
    top['ROA (%)'] = top['roa']
    display = top[['company','country','Revenue (USDm)','ROA (%)','Trend','quadrant','risk_score','Risk']].rename(columns={
        'company':'Company','country':'Country','quadrant':'Quadrant','risk_score':'Risk score'})
    st.dataframe(display, use_container_width=True, hide_index=True)
    definition(
        "Risk score is a 0–100 composite blending Size (35%), Performance (30%), Leverage (15%) "
        "and Emissions intensity (20%). Trend arrows come from a 3-year OLS slope on ROA: "
        "🔻 deteriorating, 🔺 improving, ➡️ stable. Higher score = more supervisory attention warranted.")

    msg = []
    for c in COUNTRIES:
        agg = countries.get(c, {})
        lst = agg.get('fiscal_risk_companies') or []
        if lst:
            msg.append(f"**{c} — fiscal-risk SOEs**: " + ", ".join(lst))
    if msg:
        st.warning(" &nbsp; · &nbsp; ".join(msg))

# ============================================================
# TAB 2 — COUNTRY BENCHMARK
# ============================================================
with tabs[1]:
    st.markdown("### Country benchmark")
    st.caption("Aggregates are asset- or revenue-weighted (Σ of numerator ÷ Σ of denominator) (not median).")

    rows = []
    for c in COUNTRIES:
        a = countries.get(c)
        if not a: continue
        rows.append({
            'Country': c,
            'N SOEs': a['n_soes'],
            'Combined Revenue (USDbn)': round(a['agg_revenue_usd']/1000, 2),
            'Combined Assets (USDbn)':  round(a['agg_assets_usd']/1000, 2) if a['agg_assets_usd'] else None,
            'Combined Debt (USDbn)':    round(a['agg_debt_usd']/1000, 2) if a['agg_debt_usd'] else None,
            'Portfolio ROA (%)': a['agg_roa'],
            'Portfolio Debt/Equity (×)': a['agg_leverage'],
            'Carbon intensity (tCO₂/USDmn rev)': a['agg_emissions_intensity'],
            'Top-3 revenue share (%)': a['top3_revenue_share'],
            'Scope 1 (Mt)': round(a['agg_emissions_t']/1e6, 2) if a.get('agg_emissions_t') else None,
            'Fiscal-risk SOEs (count)': a['n_fiscal_risk'],
        })
    bench = pd.DataFrame(rows).set_index('Country').T
    st.dataframe(bench, use_container_width=True)
    definition(
        "Portfolio ROA = Σ(Net Profit) ÷ Σ(Total Assets) — asset-weighted, not averaged, so "
        "big SOEs pull the number. Debt/Equity (Investopedia) = Σ(Debt) ÷ Σ(Equity); values > 2× "
        "signal high leverage. Carbon intensity = Scope 1 ÷ Revenue; lower = cleaner production. "
        "Top-3 share is the % of portfolio revenue captured by the three largest SOEs.")

    st.markdown("---")

    # Quadrant share comparison
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Portfolio mix by quadrant")
        qd = soe_df.dropna(subset=['revenue_usd']).groupby(['country','quadrant'])['revenue_usd'].sum().reset_index()
        qd['share'] = qd.groupby('country')['revenue_usd'].transform(lambda x: x/x.sum()*100)
        fig = px.bar(qd, x='country', y='share', color='quadrant',
                     color_discrete_map=QUAD_COLOR,
                     labels={'share':'Share of SOE revenue (%)','country':''},
                     text=qd['share'].round(0).astype(str)+'%')
        fig.update_traces(textposition='inside')
        fig.update_layout(height=420, barmode='stack')
        st.plotly_chart(fig, use_container_width=True)
        definition(
            "Bars show the share of each country's SOE revenue sitting in each quadrant of the "
            "Size × ROA map. A large red slice = fiscal-risk weight; a large green slice = "
            "portfolio dominated by profitable large SOEs.")

    with col_r:
        st.markdown("#### Transition exposure")
        td = soe_df.groupby(['country','transition_category']).size().reset_index(name='n')
        fig = px.bar(td, x='country', y='n', color='transition_category',
                     color_discrete_map=TRANS_COLOR,
                     labels={'n':'Number of SOEs','country':''})
        fig.update_layout(height=420, barmode='stack')
        st.plotly_chart(fig, use_container_width=True)
        definition(
            "Count of SOEs per transition category. <b>Liability</b> = high-carbon AND loss-making "
            "(decarbonise-or-restructure candidate); <b>Opportunity</b> = high-carbon AND profitable "
            "(investable for green capex since cash flow supports debt service).")

    st.markdown("#### Concentration")
    st.caption("Share of SOE revenue captured by the largest SOEs. High concentration means fiscal risk is actually a bet on one or two firms.")

    col_a, col_b = st.columns(2)
    with col_a:
        concrows = []
        for c in COUNTRIES:
            recs = soe_df[soe_df['country']==c].dropna(subset=['revenue_usd']).sort_values('revenue_usd', ascending=False)
            total = recs['revenue_usd'].sum()
            for n in [1,2,5]:
                sh = recs.head(n)['revenue_usd'].sum()/total*100 if total else None
                concrows.append({'Country': c, 'Top N': f'Top {n}', 'Share of portfolio revenue (%)': round(sh,1) if sh else None})
        conc = pd.DataFrame(concrows)
        fig = px.bar(conc, x='Top N', y='Share of portfolio revenue (%)', color='Country',
                     color_discrete_map=COUNTRY_COLOR, barmode='group',
                     text='Share of portfolio revenue (%)')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=380, yaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)
        definition(
            "Share of SOE revenue in the largest 1, 2 and 5 firms. If Top 1 is already > 50%, "
            "fiscal risk is effectively single-name risk — one large SOE shock moves the whole portfolio.")

    with col_b:
        # Lorenz-style cumulative concentration curve
        fig = go.Figure()
        for c in COUNTRIES:
            col = COUNTRY_COLOR[c]
            recs = soe_df[soe_df['country']==c].dropna(subset=['revenue_usd']).sort_values('revenue_usd', ascending=False)
            total = recs['revenue_usd'].sum()
            if total == 0 or len(recs) == 0: continue
            cum = (recs['revenue_usd'].cumsum() / total * 100).tolist()
            xs = [0] + [(i+1)/len(recs)*100 for i in range(len(recs))]
            ys = [0] + cum
            fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines+markers', name=c,
                                     line=dict(color=col, width=2.5)))
        fig.add_trace(go.Scatter(x=[0,100], y=[0,100], mode='lines',
                                 line=dict(color='#bbbbbb', dash='dash', width=1),
                                 name='Perfectly even', hoverinfo='skip'))
        fig.update_layout(
            height=380,
            xaxis_title='Cumulative share of SOEs (ranked by revenue, %)',
            yaxis_title='Cumulative share of portfolio revenue (%)',
            xaxis_range=[0,100], yaxis_range=[0,105],
            legend=dict(orientation='h', yanchor='bottom', y=-0.25))
        st.plotly_chart(fig, use_container_width=True)
        definition(
            "Lorenz-style curve: each point answers 'the top X% of SOEs earn Y% of portfolio revenue'. "
            "The dashed 45° line is a perfectly even portfolio. The more the curve bows toward the top-left, "
            "the more concentrated the portfolio is. (Investopedia: Lorenz curve.)")

# ============================================================
# TAB 3 — TRANSITION
# ============================================================
with tabs[2]:
    st.markdown("### Transition lens")
    st.caption("Scope 1 emissions and emissions intensity. The graph answers the following question: which SOEs are a *liability* (high-carbon + weak returns → drag on the balance sheet under decarbonisation) and which are an *opportunity* (high-carbon but profitable → investable candidate for green capex).")

    emi_soes = soe_df.dropna(subset=['scope1_tonnes']).copy()

    # KPI strip
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("SOEs with Scope 1 data", len(emi_soes))
    k2.metric("Combined Scope 1", f"{emi_soes['scope1_tonnes'].sum()/1e6:.1f} MtCO₂e")
    top_emitter = emi_soes.sort_values('scope1_tonnes', ascending=False).iloc[0]
    k3.metric("Largest emitter", top_emitter['company'][:20],
              f"{top_emitter['scope1_tonnes']/1e6:.1f} Mt")
    liability_n = (emi_soes['transition_category']=='Transition liability').sum()
    k4.metric("Transition liabilities", int(liability_n),
              help="High-carbon SOEs with low profitability")

    st.markdown("---")

    # Liability / opportunity quadrant
    st.markdown("#### Liability vs Opportunity — Emissions intensity × ROA")
    d = emi_soes.dropna(subset=['emissions_intensity','roa']).copy()
    # label only the top emitters (by Scope 1 tonnage) — avoid clutter
    top_emitters = set(d.sort_values('scope1_tonnes', ascending=False).head(5)['company'])
    d['label'] = d['company'].apply(lambda c: c if c in top_emitters else '')

    fig = px.scatter(d, x='emissions_intensity', y='roa',
                     color='transition_category', color_discrete_map=TRANS_COLOR,
                     size='revenue_usd', size_max=55,
                     hover_name='company',
                     text='label',
                     custom_data=['country','scope1_tonnes','revenue_usd'],
                     labels={'emissions_intensity':'Emissions intensity (tCO₂ / USDmn revenue)',
                             'roa':'ROA (%)'},
                     log_x=True)
    fig.update_traces(
        textposition='top center', textfont=dict(size=11),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Country: %{customdata[0]}<br>"
            "Scope 1: %{customdata[1]:,.0f} tCO₂e<br>"
            "Revenue: $%{customdata[2]:,.0f} mn<br>"
            "Intensity: %{x:.0f} tCO₂/USDmn<br>"
            "ROA: %{y:.1f}%<extra></extra>"))
    fig.add_vline(x=500, line_dash='dot', line_color='#888', opacity=0.6,
                  annotation_text='500 tCO₂/USDmn', annotation_position='top right')
    fig.add_hline(y=0, line_dash='dot', line_color='#888', opacity=0.6,
                  annotation_text='ROA = 0', annotation_position='bottom right')
    fig.add_hline(y=2, line_dash='dot', line_color='#888', opacity=0.6,
                  annotation_text='ROA = 2% (opportunity threshold)', annotation_position='top right')
    fig.update_layout(height=520, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
    definition(
        "X = tCO₂ per USD million of revenue (log). Y = ROA (Net Profit ÷ Assets, Investopedia). "
        "Bubble size = revenue so scale is on equal visual footing. "
        "Top-right of the red vertical = high-carbon SOEs; below ROA=0 they are transition liabilities, "
        "above ROA=2% they are transition opportunities. Labels shown for the top 5 emitters only.")

    st.markdown("---")

    # Intensity ranking
    st.markdown("#### Emissions-intensity ranking")
    rank_log = st.toggle("Log scale (X)", value=True, key='rank_log',
                         help="Values span two orders of magnitude (NIS ~29 → EPS ~4,500). "
                              "Log spreads the low-intensity SOEs apart.")
    rank = emi_soes.dropna(subset=['emissions_intensity']).sort_values('emissions_intensity', ascending=True)
    fig = px.bar(rank, x='emissions_intensity', y='company', color='country', orientation='h',
                 color_discrete_map=COUNTRY_COLOR,
                 text=rank['emissions_intensity'].round(0).astype(int).astype(str),
                 log_x=rank_log,
                 labels={'emissions_intensity':'tCO₂ per USD million revenue' + (' (log)' if rank_log else ''),
                         'company':''})
    fig.update_traces(textposition='outside')
    fig.update_layout(height=max(300, 40*len(rank)), margin=dict(l=10,r=60,t=10,b=20))
    st.plotly_chart(fig, use_container_width=True)
    definition(
        "Emissions intensity = Scope 1 tonnes ÷ revenue (USDmn). Lower is cleaner. "
        "(Investopedia: carbon intensity is emissions per unit of economic output.)")

    # Compute concentration stat for the strong callout
    srt_emi = emi_soes.sort_values('scope1_tonnes', ascending=False)
    total_t = srt_emi['scope1_tonnes'].sum()
    top3_pct = srt_emi.head(3)['scope1_tonnes'].sum() / total_t * 100 if total_t else 0
    top3_names = ", ".join(srt_emi.head(3)['company'].tolist())
    st.markdown("#### Concentration of portfolio emissions")
    st.error(
        f"**>{top3_pct:.0f}% of Scope 1 emissions sit in just 3 SOEs** "
        f"({top3_names}). Transition policy here is firm-specific, not portfolio-wide.")
    emi_soes_sorted = emi_soes.sort_values('scope1_tonnes', ascending=False)
    rows = []
    for c in COUNTRIES:
        ccountry = emi_soes_sorted[emi_soes_sorted['country']==c]
        total = ccountry['scope1_tonnes'].sum()
        if total == 0 or len(ccountry) == 0: continue
        for n in [1,3]:
            share = ccountry.head(n)['scope1_tonnes'].sum()/total*100
            rows.append({'Country': c, 'Top N': f'Top {n}',
                         'Share of Scope 1 (%)': round(share,1)})
    concEmi = pd.DataFrame(rows)
    fig = px.bar(concEmi, x='Top N', y='Share of Scope 1 (%)', color='Country',
                 color_discrete_map=COUNTRY_COLOR, barmode='group',
                 text='Share of Scope 1 (%)')
    fig.update_traces(textposition='outside')
    fig.update_layout(height=340, yaxis_range=[0, 105])
    st.plotly_chart(fig, use_container_width=True)
    definition(
        "Share of country-level Scope 1 emissions captured by the top 1 and top 3 SOEs. "
        "The closer the bars are to 100%, the more single-firm the decarbonisation decision is.")

# ============================================================
# TAB 4 — TRENDS
# ============================================================
with tabs[3]:
    st.markdown("### Trends over time — with direction flags")
    st.caption("A 3-year OLS slope is fitted per SOE to ROA, Revenue and Net Margin and converted into a direction flag (deteriorating / improving / stable). Below we focus on the SOEs that actually matter for fiscal risk — the large ones.")

    # ---- Summary block: how many large / high-risk SOEs are deteriorating
    # "Large" = above-median revenue; "High risk" = risk_score >= 70
    rev_med_trend = soe_df['revenue_usd'].dropna().median()
    large = soe_df[soe_df['revenue_usd'] >= rev_med_trend] if rev_med_trend else soe_df.iloc[0:0]
    high_risk = soe_df[soe_df['risk_score'].fillna(0) >= 70]

    def det_count(subset):
        return int((subset['roa_direction'] == 'deteriorating').sum())
    def total_with_flag(subset):
        return int((subset['roa_direction'].isin(['deteriorating','improving','stable'])).sum())

    s1, s2, s3 = st.columns(3)
    s1.metric("Large SOEs deteriorating (ROA)",
              f"{det_count(large)} / {total_with_flag(large)}",
              help="Large = revenue above the portfolio median. Counted against SOEs with ≥3 years of ROA data.")
    s2.metric("High-risk SOEs deteriorating (ROA)",
              f"{det_count(high_risk)} / {total_with_flag(high_risk)}",
              help="High-risk = composite risk score ≥ 70.")
    s3.metric("Fiscal-risk quadrant deteriorating (ROA)",
              f"{det_count(soe_df[soe_df['quadrant']=='Fiscal risk'])} / {total_with_flag(soe_df[soe_df['quadrant']=='Fiscal risk'])}",
              help="Large SOEs that already sit in the loss-making quadrant.")
    definition(
        "Each tile reads <b>X / N</b>: out of N SOEs in that group with a usable 3-year ROA series, "
        "X are on a deteriorating trend. The middle tile is the one to watch — SOEs that are both "
        "high-risk today and getting worse are the near-term fiscal-risk candidates.")

    st.markdown("---")

    # ---- Filtered direction-flag table — NOT every SOE, only those that matter
    st.markdown("#### Direction flags — priority SOEs")

    view_choice = st.radio(
        "Show",
        ["Top 10 by revenue", "Top risk decile (score ≥ 70)", "Fiscal-risk quadrant only", "All"],
        horizontal=True, key='trend_view')

    flags = soe_df[['company','country','latest_year','roa','risk_score','quadrant',
                    'roa_slope','roa_direction','revenue_direction','margin_direction']].copy()
    if view_choice == "Top 10 by revenue":
        flags_view = soe_df.sort_values('revenue_usd', ascending=False).head(10)['company'].tolist()
        flags = flags[flags['company'].isin(flags_view)]
    elif view_choice == "Top risk decile (score ≥ 70)":
        flags = flags[flags['risk_score'].fillna(0) >= 70]
    elif view_choice == "Fiscal-risk quadrant only":
        flags = flags[flags['quadrant'] == 'Fiscal risk']

    flags['ROA trend'] = flags['roa_direction'].map(DIR_ICON).fillna('…') + ' ' + flags['roa_direction'].fillna('')
    flags['Revenue trend'] = flags['revenue_direction'].map(DIR_ICON).fillna('…') + ' ' + flags['revenue_direction'].fillna('')
    flags['Margin trend'] = flags['margin_direction'].map(DIR_ICON).fillna('…') + ' ' + flags['margin_direction'].fillna('')
    flags_disp = flags[['company','country','latest_year','roa','risk_score','quadrant',
                        'ROA trend','Revenue trend','Margin trend']].rename(columns={
        'company':'Company','country':'Country','latest_year':'Latest year',
        'roa':'ROA (%)','risk_score':'Risk score','quadrant':'Quadrant'})
    st.dataframe(flags_disp.sort_values('Risk score', ascending=False, na_position='last'),
                 use_container_width=True, hide_index=True, height=380)
    definition(
        "🔻 = deteriorating (3-yr slope ≤ −0.5 pp/year), 🔺 = improving (≥ +0.5), "
        "➡️ = stable, … = insufficient data. Rows are sorted by composite risk score.")

    st.markdown("---")

    st.markdown("#### Compare over time")
    col_l, col_r = st.columns([1,3])
    with col_l:
        indicator = st.selectbox("Indicator", [
            ('revenue_usd','Revenue (USD mn)'),
            ('net_profit_usd','Net Profit (USD mn)'),
            ('ebitda_usd','EBITDA (USD mn)'),
            ('ebitda_margin','EBITDA Margin (%)'),
            ('roa','ROA (%)'),
            ('roe','ROE (%)'),
            ('debt_to_equity','Debt/Equity (%)'),
            ('employees','Employees'),
        ], format_func=lambda x:x[1])[0]
        all_companies = sorted(df['company'].unique())
        default_comps = soe_df.sort_values('revenue_usd', ascending=False).head(6)['company'].tolist()
        selected = st.multiselect("Companies", all_companies, default=default_comps)
    with col_r:
        d = df[df['company'].isin(selected)].dropna(subset=[indicator]).sort_values('year')
        if len(d):
            fig = px.line(d, x='year', y=indicator, color='company', markers=True)
            fig.update_layout(height=520)
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "Line chart: each SOE's indicator over the years covered. "
                "Revenue in USD millions converted at annual-average FX; ratios (ROA/ROE/EBITDA margin) in %. "
                "Use this to eyeball whether a trend flag is driven by a real shift or by one volatile year.")
        else:
            st.info("No data for this selection.")

# ============================================================
# TAB 5 — DEEP DIVE (original exploratory charts)
# ============================================================
with tabs[4]:
    st.markdown("### Deep dive — exploratory charts")
    st.caption("Classical DuPont / leverage / productivity scatter views. Use the filters below to narrow down.")

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 2])
    with c1:
        years = ['Latest'] + sorted(df['year'].dropna().unique().astype(int).tolist(), reverse=True)
        year_sel = st.selectbox("Year", years, key='dd_year')
    with c2:
        country_sel = st.selectbox("Country", ["All"] + COUNTRIES, key='dd_country')
    with c3:
        sector_sel = st.selectbox("Sector", ["All"] + sorted(df['sector'].dropna().unique().tolist()), key='dd_sector')
    with c4:
        size_toggle = st.checkbox("Size bubbles by revenue", value=False, key='dd_size')

    def apply_filter(d):
        if country_sel != "All": d = d[d['country']==country_sel]
        if sector_sel != "All":  d = d[d['sector']==sector_sel]
        return d
    def latest_per_company_local(d, field=None):
        if year_sel != 'Latest':
            return d[d['year']==int(year_sel)]
        d2 = d.sort_values('year', ascending=False)
        if field: d2 = d2[d2[field].notna()]
        return d2.drop_duplicates(subset=['company'], keep='first')

    flt = apply_filter(df)
    latest_rev = latest_per_company_local(flt, 'revenue_usd')

    size_arg = 'revenue_usd' if size_toggle else None
    size_max = 40 if size_toggle else 10

    st.markdown("#### Fiscal weight & leverage")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Revenue / GDP vs Debt / Equity**")
        dd = latest_rev.dropna(subset=['debt_to_equity','revenue_pct_gdp'])
        if len(dd):
            fig = px.scatter(dd, x='debt_to_equity', y='revenue_pct_gdp', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_vline(x=100, line_dash='dot', line_color='#888', opacity=0.4,
                          annotation_text='D/E = 100%')
            fig.add_hline(y=5, line_dash='dash', line_color='#d97706', opacity=0.6,
                          annotation_text='5% GDP — fiscal relevance threshold',
                          annotation_position='top right')
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "X = Debt / Equity (Investopedia: higher = more leveraged, 100% means debt equals equity). "
                "Y = SOE revenue as % of GDP (Investopedia: fiscal weight). The orange dashed line at 5% is a "
                "rule-of-thumb threshold above which a single SOE's turnover is material to national fiscal stability.")
    with col_r:
        st.markdown("**Assets / GDP vs ROA**")
        dd = latest_rev.dropna(subset=['assets_pct_gdp','roa'])
        if len(dd):
            fig = px.scatter(dd, x='assets_pct_gdp', y='roa', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888', opacity=0.4,
                          annotation_text='ROA = 0')
            fig.add_vline(x=5, line_dash='dash', line_color='#d97706', opacity=0.6,
                          annotation_text='5% GDP — fiscal relevance threshold',
                          annotation_position='top right')
            # Annotate EPS explicitly if in the frame
            eps_row = dd[dd['company'].str.startswith('EPS')]
            if len(eps_row):
                r0 = eps_row.iloc[0]
                fig.add_annotation(
                    x=r0['assets_pct_gdp'], y=r0['roa'],
                    text='EPS — Serbia\'s largest SOE', showarrow=True,
                    arrowhead=2, ax=40, ay=-30,
                    font=dict(color='#c8102e', size=11))
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "X = total assets as % of national GDP (fiscal weight). Y = ROA (Net Profit ÷ Assets). "
                "Above the orange threshold, a single SOE's balance sheet is large enough to matter for the sovereign. "
                "Points below ROA = 0 on the right-hand side are the priority watchlist: big AND loss-making.")

    st.markdown("#### Operating efficiency")
    # DuPont decomposition callout: which low-ROA SOEs have low turnover vs low margin
    dup = latest_rev.dropna(subset=['asset_turnover','net_margin','roa']).copy()
    low_roa = dup[dup['roa'] < 2]
    turn_med = dup['asset_turnover'].median()
    margin_med = dup['net_margin'].median()
    driven_by_turnover = low_roa[(low_roa['asset_turnover'] < turn_med) & (low_roa['net_margin'] >= margin_med)]
    driven_by_margin = low_roa[(low_roa['net_margin'] < margin_med) & (low_roa['asset_turnover'] >= turn_med)]
    driven_by_both   = low_roa[(low_roa['asset_turnover'] < turn_med) & (low_roa['net_margin'] < margin_med)]

    callout = []
    if len(driven_by_turnover):
        callout.append(f"**Asset turnover** (assets sitting idle): {', '.join(driven_by_turnover['company'].head(5).tolist())}")
    if len(driven_by_margin):
        callout.append(f"**Margin** (pricing / cost issue): {', '.join(driven_by_margin['company'].head(5).tolist())}")
    if len(driven_by_both):
        callout.append(f"**Both** (structural weakness): {', '.join(driven_by_both['company'].head(5).tolist())}")
    if callout:
        st.info("**Why ROA is low — DuPont decomposition of ROA < 2% SOEs:** \n\n" + "\n\n".join(f"- {c}" for c in callout))

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**DuPont: Asset turnover vs ROA**")
        dd = latest_rev.dropna(subset=['asset_turnover','roa'])
        if len(dd):
            fig = px.scatter(dd, x='asset_turnover', y='roa', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            for margin in [0.05, 0.10, 0.20]:
                fig.add_scatter(x=[0, 2], y=[0, 2*margin*100], mode='lines',
                                line=dict(color='lightgray',dash='dot',width=1),
                                showlegend=False, hoverinfo='skip',
                                name=f'{int(margin*100)}% margin')
            fig.update_traces(textposition='top center', textfont_size=8,
                              selector=dict(mode='markers+text'))
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "DuPont identity (Investopedia): ROA = Net Margin × Asset Turnover. "
                "X = Revenue ÷ Assets; Y = ROA. The dotted rays are constant-margin lines (5%, 10%, 20%). "
                "A point with high turnover but low ROA has a margin problem; low turnover + low ROA = idle assets.")
    with col_r:
        st.markdown("**EBITDA margin vs Revenue scale (log)**")
        dd = latest_rev.dropna(subset=['ebitda_margin','revenue_usd'])
        if len(dd):
            fig = px.scatter(dd, x='revenue_usd', y='ebitda_margin', color='country',
                             color_discrete_map=COUNTRY_COLOR, log_x=True,
                             hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888')
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "X = Revenue (log); Y = EBITDA Margin = EBITDA ÷ Revenue (Investopedia: cash profitability "
                "before capex and financing). Below 0 = operating losses. Look for scale-without-margin "
                "(large revenue, flat/negative margin) as a warning.")

    st.markdown("#### Capital structure")
    # Flag over-leveraged and weak-ROE rows
    cap_d = latest_rev.dropna(subset=['debt_to_equity','roe']).copy()
    def cap_flag(r):
        over = r['debt_to_equity'] > 200
        weak = r['roe'] < 0
        if over and weak: return '🔴 Over-leveraged & loss-making'
        if over:          return '🟠 Over-leveraged (D/E > 2)'
        if weak:          return '🟡 Negative ROE'
        return '🟢 Normal'
    cap_d['flag'] = cap_d.apply(cap_flag, axis=1)
    CAP_COLOR = {'🔴 Over-leveraged & loss-making':'#d62728',
                 '🟠 Over-leveraged (D/E > 2)':'#ff7f0e',
                 '🟡 Negative ROE':'#f4c430',
                 '🟢 Normal':'#2ca02c'}
    flagged = cap_d[cap_d['flag'] != '🟢 Normal']
    if len(flagged):
        names = ", ".join(flagged.sort_values(['flag','debt_to_equity'], ascending=[True, False])['company'].tolist())
        st.warning(f"**Flagged SOEs (D/E > 2 or ROE < 0):** {names}")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**ROE vs Debt / Equity**")
        dd = cap_d.copy()
        if len(dd):
            fig = px.scatter(dd, x='debt_to_equity', y='roe', color='flag',
                             color_discrete_map=CAP_COLOR,
                             hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888')
            fig.add_vline(x=200, line_dash='dash', line_color='#d97706', opacity=0.6,
                          annotation_text='D/E = 200% (over-leveraged)')
            fig.update_layout(height=420, legend_title_text='Flag')
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "X = Debt / Equity %; Y = ROE = Net Profit ÷ Equity (Investopedia: return on state capital). "
                "The orange dashed vertical at 200% is a conventional over-leverage threshold. "
                "Points below ROE = 0 on the right of that line are the worst: levered and losing money.")
    with col_r:
        st.markdown("**Net profit vs Equity** (slope = ROE)")
        np_log = st.toggle("Log X (equity)", value=False, key='np_eq_log',
                           help="Equity varies from a few hundred mn to $20B+. Log compresses the large end.")
        dd = latest_rev.dropna(subset=['equity_usd','net_profit_usd'])
        if np_log:
            dd = dd[dd['equity_usd'] > 0]
        if len(dd):
            fig = px.scatter(dd, x='equity_usd', y='net_profit_usd', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max, log_x=np_log)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888')
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
            definition(
                "X = Equity (USD mn); Y = Net Profit (USD mn). "
                "The slope of a line from origin through a point = that SOE's ROE.")

# ============================================================
# TAB 6 — DATA TABLE
# ============================================================
with tabs[5]:
    st.markdown("### Data table")
    st.caption("All records after sanitisation. Use the presets to jump to a focused view.")

    preset = st.radio(
        "Preset view",
        ["All records", "Top risk (score ≥ 70)", "Largest SOEs (top 10 revenue)",
         "With emissions data", "Fiscal-risk quadrant"],
        horizontal=True, key='tbl_preset')

    # derive the company whitelist from analytics
    if preset == "Top risk (score ≥ 70)":
        keep = soe_df[soe_df['risk_score'].fillna(0) >= 70]['company'].tolist()
    elif preset == "Largest SOEs (top 10 revenue)":
        keep = soe_df.sort_values('revenue_usd', ascending=False).head(10)['company'].tolist()
    elif preset == "With emissions data":
        keep = soe_df.dropna(subset=['scope1_tonnes'])['company'].tolist()
    elif preset == "Fiscal-risk quadrant":
        keep = soe_df[soe_df['quadrant']=='Fiscal risk']['company'].tolist()
    else:
        keep = None

    cols = ['company','country','year','sector','currency','revenue','net_profit','ebitda','ebit',
            'total_assets','equity','total_debt','employees',
            'revenue_usd','net_profit_usd','ebitda_usd','total_assets_usd','equity_usd',
            'net_margin','ebitda_margin','roa','roe','asset_turnover','leverage_ratio','debt_to_equity',
            'revenue_pct_gdp','assets_pct_gdp','revenue_per_employee','revenue_growth']
    avail = [c for c in cols if c in df.columns]
    tbl = df[avail].copy()
    if keep is not None:
        tbl = tbl[tbl['company'].isin(keep)]
    for c in [x for x in avail if x not in ['company','country','sector','currency','year']]:
        tbl[c] = pd.to_numeric(tbl[c], errors='coerce')
    tbl = tbl.sort_values(['country','company','year'])
    st.caption(f"Showing {len(tbl)} rows across {tbl['company'].nunique()} SOEs.")
    st.dataframe(tbl, use_container_width=True, hide_index=True, height=600)
    definition(
        "One row per SOE per year. USD values use period-average FX rates (IMF IFS). "
        "ROA, ROE, margins are in %. Click a column header to sort; download the filtered view below.")
    st.download_button(
        f"Download {preset.lower()} as CSV",
        tbl.to_csv(index=False).encode('utf-8'),
        file_name=f"soe_poc_{preset.lower().replace(' ','_').replace('(','').replace(')','').replace('≥','ge').replace(',','')}.csv",
        mime='text/csv')

# ============================================================
# TAB 7 — ABOUT
# ============================================================
with tabs[6]:
    st.markdown("### About this dashboard")

    st.markdown("""
A proof-of-concept **fiscal-risk lens** over state-owned enterprises in **Serbia, Poland,
Romania and Montenegro**. The aim is to move beyond company-by-company description and point at
the slices of the portfolio where public resources are most exposed (under-performing big SOEs,
concentrated emissions, deteriorating trends). It is a first-pass instrument for PEFA PI-12-style
fiscal-risk monitoring, not a published product.

Coverage is deepest for Serbia and Poland. Romania (7 SOEs — Nuclearelectrica, Romgaz,
Transelectrica, Transgaz, Electrica, CFR, CFR Marfa) and Montenegro (15 SOEs incl. EPCG, CEDIS,
CGES, Aerodromi, Plantaže, ToMontenegro, Luka Bar) are present but thinner: most Montenegrin
rows come from iSOEF 2023 and carry revenue + total assets but no net profit, so ROA, the
quadrant classification and the risk score cannot always be computed for them. See *Known gaps*
and *Options to close the gaps* at the bottom of this tab.
""")

    st.markdown("#### Why this view")
    st.markdown("""
PEFA Pillar III (asset and liability management) and in particular **PI-12 (fiscal risk reporting)**
expects governments to have a clear picture of: (i) the economic weight of their SOE portfolio,
(ii) the subset of SOEs that are loss-making or highly leveraged, (iii) concentration of risk in
a few firms, and (iv) exposure to external shocks — including decarbonisation. The executive tab
answers those four questions at a glance.
""")

    st.markdown("#### Risk score — how it's built")
    st.markdown("""
Risk score is a **weighted composite** on a 0–100 scale (higher = more attention warranted):

| Component | Weight | Maps high risk to | Source field |
|---|---|---|---|
| Size | 35% | Revenue percentile within the portfolio | `revenue_usd` |
| Performance | 30% | ROA < 0 → 100, ROA > +10% → 0 (linear) | `roa` |
| Leverage | 15% | Debt / Total assets ≥ 80% → 100 | `total_debt_usd`, `total_assets_usd` |
| Emissions intensity | 20% | tCO₂ / USDmn revenue ≥ 2,000 → 100 | `scope1_tonnes`, `revenue_usd` |

When a component is missing (e.g. no emissions data), the remaining components are re-weighted
to sum to one. The score is intentionally simple and meant to be *readable*, not to replace
formal credit or risk analysis.
""")

    st.markdown("#### Quadrant classification")
    st.markdown("""
Each SOE is placed in one of four cells of Size × ROA:

- **Fiscal risk** — revenue above the portfolio median *and* negative ROA. These are the SOEs
  where contingent-liability risk is concentrated.
- **Strategic asset** — large and profitable. These carry scale but also the most public policy
  weight; dividend capacity lives here.
- **Small & loss-making** — minor fiscal drag individually but often cumulative in aggregate and
  politically hard to restructure.
- **Small & performing** — scale-limited, usually niche / sub-sector SOEs.
""")

    st.markdown("#### Transition categories")
    st.markdown("""
For SOEs with Scope 1 data we layer a transition view:

- **Transition liability** — emissions intensity > 500 tCO₂/USDmn **and** ROA < 2%. High carbon,
  low returns — restructuring, divestment or heavy green-capex candidate.
- **Transition opportunity** — emissions intensity > 500 but ROA ≥ 2%. Profitable today, at
  risk tomorrow without decarbonisation investment. Best candidate for green financing where the
  cash flow supports debt service.
- **Low transition exposure** — emissions intensity < 500.
- **Not covered** — no Scope 1 record matched.
""")

    st.markdown("#### Trend flags")
    st.markdown("""
For each SOE we fit an OLS slope over the last three available years for ROA, revenue (USD) and
net margin. If the slope is:

- below –0.5 pp/year → 🔻 **deteriorating**
- above +0.5 pp/year → 🔺 **improving**
- otherwise → ➡️ **stable**

When fewer than three usable points exist the flag is shown as "insufficient data".
""")

    st.markdown("#### Aggregation rules (why not medians)")
    st.markdown("""
Country-level ROA, leverage and carbon intensity are reported as **weighted aggregates**:

- Portfolio ROA = Σ(Net profit) ÷ Σ(Total assets)
- Portfolio Debt/Equity = Σ(Debt) ÷ Σ(Equity)
- Portfolio carbon intensity = Σ(Scope 1) ÷ Σ(Revenue)

These match what the state actually carries on its books. Medians can be pulled around by small
SOEs and tend to misrepresent portfolio-level exposure.
""")

    st.markdown("#### Key terms")
    st.markdown("""
- **EPS (Consolidated)** — *Elektroprivreda Srbije* group statements (parent + subsidiaries:
  generation, distribution, supply). Best representation of the EPS group's economic footprint.
- **EPS (Standalone)** — EPS parent only. Useful for dividend-to-state analysis; systematically
  smaller than the consolidated view.
- **Scope 1 emissions** — direct emissions from sources the company owns or controls (plant
  combustion, owned aircraft fuel). Excludes purchased electricity (Scope 2) and value-chain (Scope 3).
- **Emissions intensity** — Scope 1 emissions ÷ revenue, reported in *tCO₂ per USD million of
  revenue*.
""")

    st.markdown("#### Data sources")
    st.markdown("""
- **Financial data** — `SOE_Master_Database_Global.xlsx`. Consolidated group-level figures from
  audited annual reports, Q4/annual financial supplements, and regulator filings. Source PDF and
  page are tracked for every record. Currencies: PLN (Poland), RSD (Serbia); values stored in
  local-currency millions and cross-normalised to USD millions using period-average FX.
- **Scope 1 emissions** — `soe specific.xlsx` sheet *RSPOL*. Facility-level Scope 1 CO₂-equivalent
  emissions aggregated to parent SOE (subsidiaries not re-added on top of the group parent, which
  already reports consolidated Scope 1).
- **GDP** — World Bank national accounts, current USD, used only for Revenue/GDP and Assets/GDP.
- **FX rates** — IMF IFS annual averages.
""")

    st.markdown("#### Processing & data quality")
    st.markdown("""
1. **Unit-mismatch detection** — records where Revenue ÷ Total Assets falls outside 0.005–10 have
   balance-sheet fields nulled (source mixed units).
2. **Implausible ratios** — ROA/ROE/margin values outside ±100% (±200% for ROE) are treated as
   data errors and hidden.
3. **Duplicate year rows** — row with the most filled fields wins.
4. **Emissions aggregation** — parent-entity Scope 1 only; subsidiaries never re-added.
5. **Dual EPS reporting** — consolidated and standalone are both kept, explicitly labelled.
6. **Government rollups** — removed from the emissions file to keep comparison at company level.
""")

    st.markdown("#### Known gaps")
    st.markdown("""
- **Emissions coverage** limited to Serbia + Poland at the moment (8 matched SOEs: PGE, Enea,
  LOT, JSW, Tauron, EPS, Air Serbia, NIS). Romanian and Montenegrin SOEs appear as *Not covered*
  in the transition tab. EU ETS and Climate TRACE are the obvious next sources to plug.
- **Romania** — 7 SOEs in the panel, but coverage is uneven: revenue is missing for CFR / CFR Marfa
  (balance-sheet-only rows), total assets are missing for Romgaz, and Electrica / Transelectrica /
  Transgaz only have partial year coverage. Investor-relations pages (BVB-listed) are the fix.
- **Montenegro** — 15 SOEs in the panel, but most 2023 rows come from iSOEF and carry revenue +
  total assets only (no net profit), so ROA / quadrant / risk score cannot be computed. EPCG is
  the only Montenegrin SOE with full data.
- TAURON group Scope 1 is under-represented (only the small *TAURON Wydobycie* subsidiary appears
  with a non-zero figure in the source).
- Employee counts are incomplete for several Polish SOEs; revenue-per-employee is missing for
  some rows.
- ORLEN 2017–2022 figures come from Q4 report "Selected Data" sections; 2022 uses post-Lotos
  restated numbers, earlier years are pre-merger and not directly comparable in absolute terms.
""")

    st.markdown("#### Options to close the gaps")
    st.markdown("""
Concrete ways to widen coverage and raise data quality, in rough order of effort:

- **Company disclosures (primary)** — pull annual reports, sustainability/ESG reports and Scope 1
  breakdowns directly from SOE investor-relations pages (ORLEN, KGHM, PGE, PZU, PKO, Enea, etc.).
  Highest authority, usually in English.
- **National registers and statistical offices** — Serbia APR (Agencija za privredne registre),
  Poland KRS + GUS, Czech Obchodní rejstřík, Romanian ONRC. Machine-readable filings, gap-filler
  for unlisted SOEs.
- **Multilateral and supranational** — WB iSOEF country reports, IMF Article IV staff reports,
  OECD SOE Scoreboard / OECD PMR, EU Commission country reports and Fiscal Stability Reports.
  Good for cross-country comparability and policy framing.
- **Regulatory / sectoral bodies** — national energy regulators (URE Poland, AERS Serbia), Eurostat
  SBS for sector aggregates, EU ETS registry for verified Scope 1 CO₂.
- **Commercial databases** — Orbis (Bureau van Dijk), S&P Capital IQ, Refinitiv; complete panel
  data but paid.
- **Open-source trackers** — Wikidata for SOE metadata (ownership %, sector codes), Global Energy
  Monitor for plant-level capacity, Climate TRACE for independent emissions estimates, OpenCorporates
  for ownership chains.
- **Internal Bank sources** — colleagues in the country teams (CMU, MTI, EFI), task team leaders
  on active operations, and PIM/PAG specialists often hold unpublished SOE data.
- **Wikipedia / press** — useful for reconciling names, scoping mergers/spin-offs, and flagging
  recent events; not citable as a primary source but a fast starting point.
""")

