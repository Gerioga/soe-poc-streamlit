"""
SOE Proof of Concept Dashboard — Serbia & Poland
Fiscal-risk oriented redesign.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os

st.set_page_config(page_title="SOE Fiscal Risk — Serbia & Poland", layout="wide", initial_sidebar_state="collapsed")

# ================ AUTH ================
PASSWORD = "Arlington"
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("## SOE Fiscal Risk — Serbia & Poland")
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

@st.cache_data
def load_financial():
    with open(os.path.join(BASE, 'financial.json'), 'r', encoding='utf-8') as f:
        return pd.DataFrame(json.load(f))

@st.cache_data
def load_emissions():
    with open(os.path.join(BASE, 'emissions.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_analytics():
    with open(os.path.join(BASE, 'analytics.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

df = load_financial()
em = load_emissions()
an = load_analytics()
em_df = pd.DataFrame(em['companies'])
soe_df = pd.DataFrame(an['soes'])

SRB_COLOR = '#c8102e'
POL_COLOR = '#005288'
COUNTRY_COLOR = {'Serbia': SRB_COLOR, 'Poland': POL_COLOR}
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

st.markdown('<p class="big-title">SOE Fiscal Risk Lens — Serbia & Poland</p>', unsafe_allow_html=True)
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

    # ---- KPI row per country
    col_l, col_r = st.columns(2)
    def kpi_card(col, c):
        a = countries[c]
        with col:
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
            k8.metric("Scope 1 emissions", f"{a['agg_emissions_t']/1e6:.1f} MtCO₂e")

    kpi_card(col_l, 'Serbia')
    kpi_card(col_r, 'Poland')

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

    fiscal_risks_srb = countries['Serbia']['fiscal_risk_companies']
    fiscal_risks_pol = countries['Poland']['fiscal_risk_companies']
    if fiscal_risks_srb or fiscal_risks_pol:
        msg = []
        if fiscal_risks_pol:
            msg.append(f"**Poland — fiscal-risk SOEs**: " + ", ".join(fiscal_risks_pol))
        if fiscal_risks_srb:
            msg.append(f"**Serbia — fiscal-risk SOEs**: " + ", ".join(fiscal_risks_srb))
        st.warning(" &nbsp; · &nbsp; ".join(msg))

# ============================================================
# TAB 2 — COUNTRY BENCHMARK
# ============================================================
with tabs[1]:
    st.markdown("### Country benchmark")
    st.caption("Aggregates are asset- or revenue-weighted (Σ of numerator ÷ Σ of denominator), not medians. This avoids small SOEs pulling the comparison away from what the state actually carries on its books.")

    rows = []
    for c in ['Serbia','Poland']:
        a = countries[c]
        rows.append({
            'Country': c,
            'N SOEs': a['n_soes'],
            'Combined Revenue (USDbn)': round(a['agg_revenue_usd']/1000, 2),
            'Combined Assets (USDbn)':  round(a['agg_assets_usd']/1000, 2),
            'Combined Debt (USDbn)':    round(a['agg_debt_usd']/1000, 2),
            'Portfolio ROA (%)': a['agg_roa'],
            'Portfolio Debt/Equity (×)': a['agg_leverage'],
            'Carbon intensity (tCO₂/USDmn rev)': a['agg_emissions_intensity'],
            'Top-3 revenue share (%)': a['top3_revenue_share'],
            'Scope 1 (Mt)': round(a['agg_emissions_t']/1e6, 2),
            'Fiscal-risk SOEs (count)': a['n_fiscal_risk'],
        })
    bench = pd.DataFrame(rows).set_index('Country').T
    st.dataframe(bench, use_container_width=True)

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

    with col_r:
        st.markdown("#### Transition exposure")
        td = soe_df.groupby(['country','transition_category']).size().reset_index(name='n')
        fig = px.bar(td, x='country', y='n', color='transition_category',
                     color_discrete_map=TRANS_COLOR,
                     labels={'n':'Number of SOEs','country':''})
        fig.update_layout(height=420, barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Concentration")
    st.caption("Share of SOE revenue captured by the largest SOEs. High concentration means fiscal risk is actually a bet on one or two firms.")
    concrows = []
    for c in ['Serbia','Poland']:
        recs = soe_df[soe_df['country']==c].dropna(subset=['revenue_usd']).sort_values('revenue_usd', ascending=False)
        total = recs['revenue_usd'].sum()
        for n in [1,3,5,10]:
            sh = recs.head(n)['revenue_usd'].sum()/total*100 if total else None
            concrows.append({'Country': c, 'Top N': f'Top {n}', 'Share of portfolio revenue (%)': round(sh,1) if sh else None})
    conc = pd.DataFrame(concrows)
    fig = px.bar(conc, x='Top N', y='Share of portfolio revenue (%)', color='Country',
                 color_discrete_map=COUNTRY_COLOR, barmode='group',
                 text='Share of portfolio revenue (%)')
    fig.update_traces(textposition='outside')
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 3 — TRANSITION
# ============================================================
with tabs[2]:
    st.markdown("### Transition lens")
    st.caption("Scope 1 emissions and emissions intensity. The policy question is: which SOEs are a *liability* (high-carbon + weak returns → drag on the balance sheet under decarbonisation) and which are an *opportunity* (high-carbon but profitable → investable candidate for green capex).")

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
    fig = px.scatter(d, x='emissions_intensity', y='roa',
                     color='transition_category', color_discrete_map=TRANS_COLOR,
                     size='scope1_tonnes', size_max=55,
                     hover_name='company',
                     custom_data=['country','scope1_tonnes','revenue_usd'],
                     labels={'emissions_intensity':'Emissions intensity (tCO₂ / USDmn revenue)',
                             'roa':'ROA (%)'},
                     log_x=True)
    fig.update_traces(hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "Country: %{customdata[0]}<br>"
        "Scope 1: %{customdata[1]:,.0f} tCO₂e<br>"
        "Revenue: $%{customdata[2]:,.0f} mn<br>"
        "Intensity: %{x:.0f} tCO₂/USDmn<br>"
        "ROA: %{y:.1f}%<extra></extra>"
    ))
    fig.add_hline(y=2, line_dash='dot', line_color='#888', opacity=0.5,
                  annotation_text='ROA = 2%')
    fig.add_vline(x=500, line_dash='dot', line_color='#888', opacity=0.5,
                  annotation_text='500 tCO₂/USDmn')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Intensity ranking
    st.markdown("#### Emissions-intensity ranking")
    rank = emi_soes.dropna(subset=['emissions_intensity']).sort_values('emissions_intensity', ascending=True)
    fig = px.bar(rank, x='emissions_intensity', y='company', color='country', orientation='h',
                 color_discrete_map=COUNTRY_COLOR,
                 text=rank['emissions_intensity'].round(0).astype(int).astype(str),
                 labels={'emissions_intensity':'tCO₂ per USD million revenue','company':''})
    fig.update_traces(textposition='outside')
    fig.update_layout(height=max(300, 40*len(rank)), margin=dict(l=10,r=60,t=10,b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Concentration of portfolio emissions")
    st.caption("In both countries, Scope 1 is concentrated in a handful of power / coal SOEs. Transition policy decisions hinge on them, not on the long tail.")
    emi_soes_sorted = emi_soes.sort_values('scope1_tonnes', ascending=False)
    rows = []
    for c in ['Serbia','Poland']:
        ccountry = emi_soes_sorted[emi_soes_sorted['country']==c]
        total = ccountry['scope1_tonnes'].sum()
        if total == 0: continue
        for n in [1,3]:
            share = ccountry.head(n)['scope1_tonnes'].sum()/total*100
            rows.append({'Country': c, 'Top N': f'Top {n}',
                         'Share of Scope 1 (%)': round(share,1)})
    concEmi = pd.DataFrame(rows)
    fig = px.bar(concEmi, x='Top N', y='Share of Scope 1 (%)', color='Country',
                 color_discrete_map=COUNTRY_COLOR, barmode='group',
                 text='Share of Scope 1 (%)')
    fig.update_traces(textposition='outside')
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 4 — TRENDS
# ============================================================
with tabs[3]:
    st.markdown("### Trends over time — with direction flags")
    st.caption("Line charts with a 3-year OLS slope converted into a direction flag. Deteriorating / improving based on ROA slope of ≥0.5 pp per year.")

    # direction flag table
    flags = soe_df[['company','country','latest_year','roa','roa_slope','roa_direction',
                    'revenue_slope_usd','revenue_direction','margin_slope','margin_direction']].copy()
    flags['ROA trend'] = flags['roa_direction'].map(DIR_ICON).fillna('…') + ' ' + flags['roa_direction'].fillna('')
    flags['Revenue trend'] = flags['revenue_direction'].map(DIR_ICON).fillna('…') + ' ' + flags['revenue_direction'].fillna('')
    flags['Margin trend'] = flags['margin_direction'].map(DIR_ICON).fillna('…') + ' ' + flags['margin_direction'].fillna('')
    flags_disp = flags[['company','country','latest_year','roa','ROA trend','Revenue trend','Margin trend']].rename(columns={
        'company':'Company','country':'Country','latest_year':'Latest year','roa':'ROA (%)'})
    st.markdown("#### Direction flags by SOE")
    st.dataframe(flags_disp.sort_values(['Country','Company']), use_container_width=True, hide_index=True, height=400)

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
        country_sel = st.selectbox("Country", ["Both", "Serbia", "Poland"], key='dd_country')
    with c3:
        sector_sel = st.selectbox("Sector", ["All"] + sorted(df['sector'].dropna().unique().tolist()), key='dd_sector')
    with c4:
        size_toggle = st.checkbox("Size bubbles by revenue", value=False, key='dd_size')

    def apply_filter(d):
        if country_sel != "Both": d = d[d['country']==country_sel]
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
            fig.add_vline(x=100, line_dash='dot', line_color='#888', opacity=0.4)
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("**Assets / GDP vs ROA**")
        dd = latest_rev.dropna(subset=['assets_pct_gdp','roa'])
        if len(dd):
            fig = px.scatter(dd, x='assets_pct_gdp', y='roa', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888', opacity=0.4)
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Operating efficiency")
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
                                showlegend=False, hoverinfo='skip')
            fig.update_traces(textposition='top center', textfont_size=8,
                              selector=dict(mode='markers+text'))
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
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

    st.markdown("#### Capital structure")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**ROE vs Debt / Equity**")
        dd = latest_rev.dropna(subset=['debt_to_equity','roe'])
        if len(dd):
            fig = px.scatter(dd, x='debt_to_equity', y='roe', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888')
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("**Net profit vs Equity** (slope = ROE)")
        dd = latest_rev.dropna(subset=['equity_usd','net_profit_usd'])
        if len(dd):
            fig = px.scatter(dd, x='equity_usd', y='net_profit_usd', color='country',
                             color_discrete_map=COUNTRY_COLOR, hover_name='company', text='company',
                             size=size_arg, size_max=size_max)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.add_hline(y=0, line_dash='dot', line_color='#888')
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB 6 — DATA TABLE
# ============================================================
with tabs[5]:
    st.markdown("### Data table")
    st.caption("All records after sanitisation. Sort/filter by clicking column headers. Export via the download button.")
    cols = ['company','country','year','sector','currency','revenue','net_profit','ebitda','ebit',
            'total_assets','equity','total_debt','employees',
            'revenue_usd','net_profit_usd','ebitda_usd','total_assets_usd','equity_usd',
            'net_margin','ebitda_margin','roa','roe','asset_turnover','leverage_ratio','debt_to_equity',
            'revenue_pct_gdp','assets_pct_gdp','revenue_per_employee','revenue_growth']
    avail = [c for c in cols if c in df.columns]
    tbl = df[avail].copy()
    for c in [x for x in avail if x not in ['company','country','sector','currency','year']]:
        tbl[c] = pd.to_numeric(tbl[c], errors='coerce')
    tbl = tbl.sort_values(['country','company','year'])
    st.dataframe(tbl, use_container_width=True, hide_index=True, height=600)
    st.download_button("Download as CSV", tbl.to_csv(index=False).encode('utf-8'),
                       file_name='soe_poc_dataset.csv', mime='text/csv')

# ============================================================
# TAB 7 — ABOUT
# ============================================================
with tabs[6]:
    st.markdown("### About this dashboard")

    st.markdown("""
A proof-of-concept **fiscal-risk lens** over state-owned enterprises in Serbia and Poland.
The aim is to move beyond company-by-company description and point at the slices of the
portfolio where public resources are most exposed (under-performing big SOEs, concentrated
emissions, deteriorating trends). It is a first-pass instrument for PEFA PI-12-style fiscal-risk
monitoring, not a published product.
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
- Emissions matching limited to 8 SOEs where a Scope 1 record existed in the source (PGE, Enea,
  LOT, JSW, Tauron, EPS, Air Serbia, NIS). The rest show as *Not covered*.
- TAURON group Scope 1 is under-represented (only the small *TAURON Wydobycie* subsidiary appears
  with a non-zero figure in the source).
- Employee counts are incomplete for several Polish SOEs; revenue-per-employee is missing for
  some rows.
- ORLEN 2017–2022 figures come from Q4 report "Selected Data" sections; 2022 uses post-Lotos
  restated numbers, earlier years are pre-merger and not directly comparable in absolute terms.

*Dashboard build: April 2026. Proof of concept — contact for data refresh or scope extension.*
""")
