"""
SOE Proof of Concept Dashboard — Serbia & Poland
Streamlit app with password gate.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os

st.set_page_config(page_title="SOE POC — Serbia & Poland", layout="wide", initial_sidebar_state="collapsed")

# ================ AUTH ================
PASSWORD = "Arlington"
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("## SOE Proof of Concept — Serbia & Poland")
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
        rows = json.load(f)
    return pd.DataFrame(rows)

@st.cache_data
def load_emissions():
    with open(os.path.join(BASE, 'emissions.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

df = load_financial()
em = load_emissions()
em_df = pd.DataFrame(em['companies'])

SRB_COLOR = '#c8102e'
POL_COLOR = '#005288'
COUNTRY_COLOR = {'Serbia': SRB_COLOR, 'Poland': POL_COLOR}

# ================ HEADER + CONTROLS ================
st.markdown("""
<style>
.big-title {font-size:28px; font-weight:700; margin-bottom:0;}
.subtitle  {color:#64748b; font-size:14px; margin-top:0;}
.stTabs [data-baseweb="tab"] {padding: 8px 18px; font-size:14px;}
div[data-testid="stMetricValue"] {font-size:22px !important;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-title">SOE Proof of Concept — Serbia & Poland</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Financial indicators + Scope 1 emissions for state-owned enterprises.</p>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 2])
with c1:
    years = ['Latest'] + sorted(df['year'].dropna().unique().astype(int).tolist(), reverse=True)
    year_sel = st.selectbox("Year", years)
with c2:
    country_sel = st.selectbox("Country", ["Both", "Serbia", "Poland"])
with c3:
    sector_sel = st.selectbox("Sector", ["All"] + sorted(df['sector'].dropna().unique().tolist()))
with c4:
    size_toggle = st.checkbox("Size bubbles by revenue", value=False)

# Filter
def apply_filter(d):
    if country_sel != "Both": d = d[d['country']==country_sel]
    if sector_sel != "All":  d = d[d['sector']==sector_sel]
    return d

# Latest-per-company helper
def latest_per_company(d, field=None):
    if year_sel != 'Latest':
        return d[d['year']==int(year_sel)]
    d = d.sort_values('year', ascending=False)
    if field:
        d = d[d[field].notna()]
    return d.drop_duplicates(subset=['company'], keep='first')

flt = apply_filter(df)
latest_rev = latest_per_company(flt, 'revenue_usd')

# ================ TABS ================
tabs = st.tabs(["Fiscal Risk", "Efficiency", "Capital Structure", "Emissions", "Trends", "Data Table", "About"])

# ---------- TAB 1: FISCAL RISK ----------
with tabs[0]:
    st.markdown("### 1. Fiscal Risk Profile")
    st.caption("How large is each SOE relative to the state's economy, and how is it financed?")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Companies", latest_rev['company'].nunique())
    k2.metric("Combined Revenue (USD)", f"${latest_rev['revenue_usd'].sum()/1000:,.1f}B")
    k3.metric("Combined Assets (USD)", f"${latest_rev['total_assets_usd'].sum()/1000:,.1f}B")
    k4.metric("Median Revenue/GDP", f"{latest_rev['revenue_pct_gdp'].median():.1f}%")
    k5.metric("Median Debt/Equity", f"{latest_rev['debt_to_equity'].median():.1f}%" if latest_rev['debt_to_equity'].notna().any() else "—")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Revenue / GDP vs Debt / Equity**")
        fig = px.scatter(latest_rev.dropna(subset=['debt_to_equity','revenue_pct_gdp']),
                         x='debt_to_equity', y='revenue_pct_gdp', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None,
                         labels={'debt_to_equity':'Debt / Equity (%)','revenue_pct_gdp':'Revenue / GDP (%)'},
                         size_max=40 if size_toggle else 10)
        fig.update_traces(textposition='top center', textfont_size=8)
        fig.add_vline(x=100, line_dash='dot', line_color='#888', opacity=0.4)
        fig.update_layout(height=420, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("**Assets / GDP vs ROA**")
        fig = px.scatter(latest_rev.dropna(subset=['assets_pct_gdp','roa']),
                         x='assets_pct_gdp', y='roa', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None,
                         labels={'assets_pct_gdp':'Assets / GDP (%)','roa':'Return on Assets (%)'},
                         size_max=40 if size_toggle else 10)
        fig.update_traces(textposition='top center', textfont_size=8)
        fig.add_hline(y=0, line_dash='dot', line_color='#888', opacity=0.4)
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Revenue by SOE (USD millions)**")
    bars = latest_rev.dropna(subset=['revenue_usd']).sort_values('revenue_usd', ascending=True)
    fig = px.bar(bars, x='revenue_usd', y='company', color='country', orientation='h',
                 color_discrete_map=COUNTRY_COLOR, height=max(300, 20*len(bars)))
    st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 2: EFFICIENCY ----------
with tabs[1]:
    st.markdown("### 2. Operating Efficiency")
    st.caption("DuPont decomposition, margin vs scale, productivity, and growth–margin positioning.")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**DuPont: Asset Turnover vs ROA** (slope = net margin)")
        fig = px.scatter(latest_rev.dropna(subset=['asset_turnover','roa']),
                         x='asset_turnover', y='roa', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
        for margin in [0.05, 0.10, 0.20]:
            xs = [0, 2]
            ys = [0, 2*margin*100]
            fig.add_scatter(x=xs, y=ys, mode='lines', line=dict(color='lightgray',dash='dot',width=1),
                            showlegend=False, hoverinfo='skip',
                            name=f'{int(margin*100)}% margin')
        fig.update_traces(textposition='top center', textfont_size=8, selector=dict(mode='markers+text'))
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("**EBITDA Margin vs Revenue Scale** (log scale)")
        d = latest_rev.dropna(subset=['ebitda_margin','revenue_usd'])
        fig = px.scatter(d, x='revenue_usd', y='ebitda_margin', color='country',
                         color_discrete_map=COUNTRY_COLOR, log_x=True,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
        fig.update_traces(textposition='top center', textfont_size=8)
        fig.add_hline(y=0, line_dash='dot', line_color='#888')
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.markdown("**Revenue per Employee vs EBITDA Margin**")
        d = latest_rev.dropna(subset=['revenue_per_employee','ebitda_margin'])
        if len(d):
            fig = px.scatter(d, x='revenue_per_employee', y='ebitda_margin', color='country',
                             color_discrete_map=COUNTRY_COLOR, log_x=True,
                             hover_name='company', text='company',
                             size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
            fig.update_traces(textposition='top center', textfont_size=8)
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough employee data for this filter.")
    with col_r2:
        st.markdown("**Revenue Growth vs EBITDA Margin** (quadrant view)")
        d = latest_rev.dropna(subset=['revenue_growth','ebitda_margin'])
        fig = px.scatter(d, x='revenue_growth', y='ebitda_margin', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
        fig.update_traces(textposition='top center', textfont_size=8)
        fig.add_hline(y=0, line_dash='dot', line_color='#888'); fig.add_vline(x=0, line_dash='dot', line_color='#888')
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 3: CAPITAL STRUCTURE ----------
with tabs[2]:
    st.markdown("### 3. Capital Structure")
    st.caption("How leverage shapes returns to the state.")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**ROE vs Debt / Equity**")
        d = latest_rev.dropna(subset=['debt_to_equity','roe'])
        fig = px.scatter(d, x='debt_to_equity', y='roe', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
        fig.update_traces(textposition='top center', textfont_size=8)
        fig.add_hline(y=0, line_dash='dot', line_color='#888')
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.markdown("**Assets/Equity (Leverage) vs ROA**")
        d = latest_rev.dropna(subset=['leverage_ratio','roa'])
        fig = px.scatter(d, x='leverage_ratio', y='roa', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
        fig.update_traces(textposition='top center', textfont_size=8)
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Net Profit vs Equity** (slope = ROE)")
    d = latest_rev.dropna(subset=['equity_usd','net_profit_usd'])
    fig = px.scatter(d, x='equity_usd', y='net_profit_usd', color='country',
                     color_discrete_map=COUNTRY_COLOR,
                     hover_name='company', text='company',
                     size='revenue_usd' if size_toggle else None, size_max=40 if size_toggle else 10)
    fig.update_traces(textposition='top center', textfont_size=8)
    fig.add_hline(y=0, line_dash='dot', line_color='#888')
    for roe in [0.05, 0.15]:
        fig.add_scatter(x=[0, d['equity_usd'].max() if len(d) else 1], y=[0, (d['equity_usd'].max() if len(d) else 1)*roe],
                        mode='lines', line=dict(color='lightgray',dash='dot',width=1), showlegend=False, hoverinfo='skip')
    fig.update_layout(height=420, xaxis_title='Equity (USD mn)', yaxis_title='Net Profit (USD mn)')
    st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 4: EMISSIONS ----------
with tabs[3]:
    st.markdown("### 4. Emissions Profile")
    st.caption("Scope 1 CO₂ equivalent emissions and carbon intensity. Data source: SOE-specific Scope 1 emissions file.")

    # Build merged emissions + latest financials
    latest_all = latest_per_company(df, 'revenue_usd')  # unfiltered latest
    merged = em_df.merge(latest_all[['company','year','revenue_usd','total_assets_usd','sector']],
                         on='company', how='left')
    merged['scope1_mt'] = merged['total_scope1'] / 1e6  # million tonnes
    merged['intensity_kgco2_per_usd'] = merged.apply(
        lambda r: r['total_scope1']/(r['revenue_usd']*1e6) if pd.notna(r['revenue_usd']) and r['revenue_usd']>0 else None, axis=1)
    # emissions per USD revenue: tCO2 / USD * 1e6 = kg/USD... let me use tCO2/USDmn for readability
    merged['tco2_per_usd_mn_rev'] = merged.apply(
        lambda r: r['total_scope1']/r['revenue_usd'] if pd.notna(r['revenue_usd']) and r['revenue_usd']>0 else None, axis=1)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("SOEs with emission data", len(merged))
    k2.metric("Total Scope 1 (MtCO₂e)", f"{merged['scope1_mt'].sum():,.1f}")
    pl_share = merged[merged['country']=='Poland']['scope1_mt'].sum() / max(1, merged['scope1_mt'].sum())*100
    k3.metric("Poland share", f"{pl_share:.0f}%")
    max_row = merged.loc[merged['scope1_mt'].idxmax()] if len(merged) else None
    if max_row is not None:
        k4.metric("Largest emitter", max_row['company'].split()[0], f"{max_row['scope1_mt']:.1f} Mt")

    # Graph 1: Bar chart of emissions per SOE
    st.markdown("**Scope 1 Emissions by SOE** (million tonnes CO₂e)")
    bars = merged.sort_values('scope1_mt', ascending=True)
    fig = px.bar(bars, x='scope1_mt', y='company', color='country', orientation='h',
                 color_discrete_map=COUNTRY_COLOR,
                 labels={'scope1_mt':'Scope 1 Emissions (MtCO₂e)','company':''},
                 text=bars['scope1_mt'].apply(lambda x: f"{x:.2f}"))
    fig.update_traces(textposition='outside')
    fig.update_layout(height=max(300, 40*len(bars)), margin=dict(l=20,r=80,t=10,b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Graph 2: Scatter — Scope 1 vs Financial indicator
    st.markdown("**Two-Way: Scope 1 Emissions vs Financial Indicator**")
    fin_choice = st.selectbox("Financial indicator (X axis)",
                              ["Revenue (USD mn)", "Total Assets (USD mn)"],
                              key='emissions_fin')
    x_col, x_label = ('revenue_usd','Revenue (USD mn)') if fin_choice.startswith('Revenue') else ('total_assets_usd','Total Assets (USD mn)')
    d = merged.dropna(subset=[x_col,'scope1_mt'])
    if len(d):
        fig = px.scatter(d, x=x_col, y='scope1_mt', color='country',
                         color_discrete_map=COUNTRY_COLOR,
                         hover_name='company', text='company',
                         log_x=True, log_y=True,
                         labels={x_col:x_label,'scope1_mt':'Scope 1 Emissions (MtCO₂e, log)'})
        fig.update_traces(textposition='top center', textfont_size=10, marker=dict(size=14))
        # reference iso-intensity lines (tCO2 per USD of revenue)
        if x_col=='revenue_usd':
            xs = [d[x_col].min(), d[x_col].max()]
            for intensity, label in [(1000, '1 kg/USD'), (100, '0.1 kg/USD'), (10, '0.01 kg/USD')]:
                ys = [xv*intensity/1e6 for xv in xs]  # scope1_mt = USDmn * tCO2/USDmn / 1e6
                fig.add_scatter(x=xs, y=ys, mode='lines',
                                line=dict(color='lightgray',dash='dot',width=1),
                                showlegend=False, hoverinfo='skip')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Distance from the diagonal = carbon intensity of revenue. Above the line = more emissions per $ of revenue.")
    else:
        st.info("Merge produced no rows with both emissions and revenue in current filter.")

    # Table: Classification by emission efficiency
    st.markdown("**Emissions Efficiency Classification**")
    st.caption("tCO₂ per USD million of revenue. Lower is better (more revenue per tonne of CO₂).")
    tbl = merged.dropna(subset=['tco2_per_usd_mn_rev']).copy()
    tbl = tbl.sort_values('tco2_per_usd_mn_rev')

    def bucket(v):
        if v is None or pd.isna(v): return '—'
        if v < 50:   return '🟢 Low intensity (< 50 tCO₂/$mn rev)'
        if v < 500:  return '🟡 Medium intensity (50–500)'
        if v < 2000: return '🟠 High intensity (500–2,000)'
        return '🔴 Very high intensity (> 2,000)'
    tbl['Class'] = tbl['tco2_per_usd_mn_rev'].apply(bucket)
    out_tbl = tbl[['company','country','sector','year','scope1_mt','revenue_usd','tco2_per_usd_mn_rev','Class']].rename(columns={
        'company':'Company','country':'Country','sector':'Sector','year':'Fin Year',
        'scope1_mt':'Scope 1 (Mt)','revenue_usd':'Revenue (USD mn)','tco2_per_usd_mn_rev':'tCO₂ / USDmn'
    })
    out_tbl['Scope 1 (Mt)']     = out_tbl['Scope 1 (Mt)'].round(2)
    out_tbl['Revenue (USD mn)'] = out_tbl['Revenue (USD mn)'].round(0)
    out_tbl['tCO₂ / USDmn']     = out_tbl['tCO₂ / USDmn'].round(0)
    st.dataframe(out_tbl, use_container_width=True, hide_index=True)

    # Show companies missing revenue merge
    missing = merged[merged['revenue_usd'].isna()]
    if len(missing):
        with st.expander("SOEs with emissions but no matched financial data"):
            st.write(missing[['company','country','scope1_mt']].to_dict('records'))

# ---------- TAB 5: TRENDS ----------
with tabs[4]:
    st.markdown("### 5. Trends Over Time")
    st.caption("Select indicator and companies to compare over years.")
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
        all_companies = sorted(flt['company'].unique())
        default_comps = sorted(flt.sort_values('year',ascending=False).drop_duplicates('company').nlargest(6,'revenue_usd')['company'].tolist())
        selected = st.multiselect("Companies", all_companies, default=default_comps)
    with col_r:
        d = flt[flt['company'].isin(selected)].dropna(subset=[indicator]).sort_values('year')
        if len(d):
            fig = px.line(d, x='year', y=indicator, color='company', markers=True)
            fig.update_layout(height=520)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for this selection.")

# ---------- TAB 6: DATA TABLE ----------
with tabs[5]:
    st.markdown("### 6. Data Table")
    st.caption("All records after sanitization. Sort/filter by clicking column headers. Export via the cloud icon top-right of the table.")
    cols = ['company','country','year','sector','currency','revenue','net_profit','ebitda','ebit',
            'total_assets','equity','total_debt','employees',
            'revenue_usd','net_profit_usd','ebitda_usd','total_assets_usd','equity_usd',
            'net_margin','ebitda_margin','roa','roe','asset_turnover','leverage_ratio','debt_to_equity',
            'revenue_pct_gdp','assets_pct_gdp','revenue_per_employee','revenue_growth']
    avail = [c for c in cols if c in flt.columns]
    tbl = flt[avail].copy()
    # Format numerics
    numeric_cols = [c for c in avail if c not in ['company','country','sector','currency','year']]
    for c in numeric_cols:
        tbl[c] = pd.to_numeric(tbl[c], errors='coerce')
    tbl = tbl.sort_values(['country','company','year'])
    st.dataframe(tbl, use_container_width=True, hide_index=True, height=600)
    st.download_button("Download as CSV", tbl.to_csv(index=False).encode('utf-8'),
                       file_name='soe_poc_dataset.csv', mime='text/csv')

# ---------- TAB 7: ABOUT ----------
with tabs[6]:
    st.markdown("### About this Dashboard")

    st.markdown("""
This proof-of-concept compares state-owned enterprises (SOEs) in **Serbia** and **Poland**
across financial performance, fiscal weight, and Scope 1 emissions. It is designed to
support internal analytical discussion, not published reporting.
""")

    st.markdown("#### What the key terms mean")
    st.markdown("""
- **EPS (Consolidated)** — *Elektroprivreda Srbije* group financial statements. Covers the parent
  JP EPS together with its subsidiaries (generation companies, distribution arm EPS Distribucija,
  supply entity EPS Snabdevanje). This is the figure that best represents the economic footprint
  of the EPS group and is what you should typically cite when comparing EPS to multinational SOEs.
- **EPS (Standalone)** — *Elektroprivreda Srbije* parent-company statements only. Shows only the
  holding/parent entity without its subsidiaries. Useful when looking at dividend capacity to the
  Serbian state or parent-level financing, but systematically smaller than the consolidated figures.
- **Scope 1 emissions** — direct greenhouse-gas emissions from sources the company owns or
  controls (e.g. combustion at thermal plants, fuel burnt by owned aircraft). Does not include
  purchased electricity (Scope 2) or value-chain emissions (Scope 3).
- **Emissions intensity** — Scope 1 emissions ÷ revenue. Reported here as *tCO₂ per USD million
  of revenue* so it is readable across SOEs of different size.
""")

    st.markdown("#### Financial indicators used")
    st.markdown("""
| Indicator | Formula | Interpretation |
|---|---|---|
| ROA | Net Profit / Total Assets | Return on the state's asset base |
| ROE | Net Profit / Equity | Return on state capital invested |
| Debt / Equity | Total Debt / Equity | Balance-sheet leverage |
| EBITDA Margin | EBITDA / Revenue | Cash profitability before capital items |
| Asset Turnover | Revenue / Total Assets | Asset productivity |
| Revenue / GDP | Revenue (USD) / GDP (USD) | Fiscal weight |
| DuPont | ROA = Net Margin × Asset Turnover | Decomposes profitability drivers |
""")

    st.markdown("#### Data sources")
    st.markdown("""
- **Financial data** — `SOE_Master_Database_Global.xlsx` (ECA_SOEs collection).
  Consolidated group-level figures extracted from audited annual reports, Q4/annual Financial
  Supplements, and regulator filings. Source PDF and page are tracked for every record.
  Currencies: **PLN** (Poland), **RSD** (Serbia). Values reported in local currency **millions**
  and cross-normalised to USD millions using period-average FX rates.
- **Scope 1 emissions** — `soe specific.xlsx` (sheet *RSPOL*). Facility-level Scope 1 CO₂
  equivalent emissions aggregated to parent SOE. Subsidiaries are rolled up into the parent
  record that already reports consolidated Scope 1, to avoid double-counting.
- **GDP** — World Bank national accounts (current USD), used only for the *Revenue/GDP* and
  *Assets/GDP* ratios.
- **FX rates** — IMF IFS annual averages, LCU per USD.
""")

    st.markdown("#### Processing and data-quality rules")
    st.markdown("""
The dashboard applies the following automated sanitisation rules when building the dataset:

1. **Unit-mismatch detection.** Records where *Revenue / Total Assets* falls outside the range
   0.005–10 have their balance-sheet fields nulled (the source row mixed units — e.g. revenue
   in full RSD but equity in millions). Better to show a blank than a misleading number.
2. **Implausible ratios nulled.** ROA / ROE / margin values outside ±100% (±200% for ROE) are
   treated as data errors and hidden.
3. **Duplicate year rows.** When the same company/year appears multiple times, the row with
   the most filled fields wins.
4. **Emissions aggregation.** Only parent-entity Scope 1 values are summed. Subsidiary records
   appearing in the source file (`PGE Energia Ciepła`, `ENEA Wytwarzanie` etc.) are *not*
   re-added on top of the group parent, which already reports consolidated emissions.
5. **EPS dual reporting.** Both *Consolidated* and *Standalone* EPS rows are kept in the
   dataset but labelled so users can see which view they are looking at.
6. **Government rollups excluded.** Rows like *Government of Poland* or *Ministry of State
   Treasury* in the emissions file are aggregates across multiple SOEs and are removed to keep
   the comparison at company level.
""")

    st.markdown("#### Known gaps")
    st.markdown("""
- Emissions matching is limited to the 8 SOEs where both a financial record and a Scope 1
  record exist (PGE, Enea, LOT, JSW, Tauron, EPS, Air Serbia, NIS). Many smaller SOEs have
  financials but no emissions data in the source file.
- TAURON group Scope 1 is reported as ~0 because only the small *TAURON Wydobycie* subsidiary
  appears in the source with a non-zero figure. The group-level figure is under-represented.
- Employee counts are incomplete for several Polish SOEs; revenue-per-employee is therefore
  missing for some rows.
- ORLEN 2017–2022 data added from quarterly reports (Q4 Selected Data). 2022 uses restated
  post-Lotos-merger figures; earlier years are pre-merger and not directly comparable in
  absolute terms.

*Dashboard build: April 2026. Contact for data updates or questions.*
""")
