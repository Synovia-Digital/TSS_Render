"""
================================================================================
  Synovia Flow -- TSS Sync Portal Dashboard (Render Cloud)
  Licensed Component: Synovia Digital Ltd
================================================================================

  Product:      Synovia Flow (Customs Declaration Management)
  Component:    TSS_Sync_Portal_Dashboard
  Version:      1.3
  Database:     Fusion_TSS_PRD (live Azure SQL)
  Schema:       PLE (Primeline Express)

  Changes v1.3:
  - Cloud deployment on Render
  - Environment variable config (no INI dependency)
  - Logos bundled in assets/ folder
  - ODBC Driver 18 for Linux

  Environment Variables Required:
      DB_SERVER    = futureworks-sdi-db.database.windows.net
      DB_NAME      = Fusion_TSS_PRD
      DB_USER      = (your SQL username)
      DB_PASSWORD  = (your SQL password)

  Usage:
      streamlit run TSS_Sync_Portal_Dashboard_v1_3.py

  Copyright (c) 2026 Synovia Digital Ltd. All rights reserved.
================================================================================
"""

import base64
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyodbc
import streamlit as st

# ==============================================================
#  IDENTITY
# ==============================================================
PROJECT     = 'TSS'
COMPONENT   = 'Sync_Portal_Dashboard'
VERSION     = '1.3'
VERSION_TAG = 'v1_3'
FULL_NAME   = f'{PROJECT}_{COMPONENT}_{VERSION_TAG}'

__version__ = VERSION
__product__ = 'Synovia Flow'
__module__  = 'TSS Sync Portal Dashboard'

# ==============================================================
#  CONFIGURATION  --  from environment variables
# ==============================================================
DB_SERVER   = os.environ.get('DB_SERVER', 'futureworks-sdi-db.database.windows.net')
DB_NAME     = os.environ.get('DB_NAME', 'Fusion_TSS_PRD')
DB_USER     = os.environ.get('DB_USER', '')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

# Assets -- relative to this script (bundled in repo)
SCRIPT_DIR     = Path(__file__).parent
ASSETS_DIR     = SCRIPT_DIR / 'assets'
FUSION_LOGO    = ASSETS_DIR / 'FusionLogo.jpg'
PRIMELINE_LOGO = ASSETS_DIR / 'PrimelineExpress.png'
SYNOVIA_LOGO   = ASSETS_DIR / 'SynoviaLogoHor.jpg'

# Also check Windows paths as fallback (local dev)
if not ASSETS_DIR.exists():
    WIN_ASSETS = Path(
        r'\\pl-az-int-prd\D_Drive\Applications\Fusion_Release_4'
        r'\Synoiva_TSS\TSS_Synoiva\Assets')
    if WIN_ASSETS.exists():
        ASSETS_DIR     = WIN_ASSETS
        FUSION_LOGO    = ASSETS_DIR / 'FusionLogo.jpg'
        PRIMELINE_LOGO = ASSETS_DIR / 'PrimelineExpress.png'
        SYNOVIA_LOGO   = ASSETS_DIR / 'SynoviaLogoHor.jpg'

# Also check for INI file (local Windows dev fallback)
INI_PATH = r'D:\confguration\fusion_TSS.ini'

STATUS_CONFIG = {
    'Arrived':                 ('✅', '#16a34a', '#f0fdf4', '#bbf7d0'),
    'Authorised for Movement': ('🛡️', '#2563eb', '#eff6ff', '#bfdbfe'),
    'Authorised for movement': ('🛡️', '#2563eb', '#eff6ff', '#bfdbfe'),
    'Draft':                   ('📝', '#d97706', '#fffbeb', '#fde68a'),
    'Submitted':               ('📤', '#7c3aed', '#f5f3ff', '#ddd6fe'),
    'Processing':              ('⏳', '#7c3aed', '#f5f3ff', '#ddd6fe'),
    'Cancelled':               ('🚫', '#6b7280', '#f9fafb', '#e5e7eb'),
    'Trader Input Required':   ('⚠️', '#ea580c', '#fff7ed', '#fed7aa'),
    'Amendment Required':      ('⚠️', '#ea580c', '#fff7ed', '#fed7aa'),
    'Rejected':                ('❌', '#dc2626', '#fef2f2', '#fecaca'),
    'Do Not Load':             ('🛑', '#dc2626', '#fef2f2', '#fecaca'),
    'Accepted':                ('✅', '#16a34a', '#f0fdf4', '#bbf7d0'),
    'Cleared':                 ('✅', '#16a34a', '#f0fdf4', '#bbf7d0'),
}
DEFAULT_STATUS = ('📋', '#6b7280', '#f9fafb', '#e5e7eb')

# ==============================================================
#  PAGE CONFIG
# ==============================================================
st.set_page_config(
    page_title=f'Synovia Flow - {COMPONENT} {VERSION_TAG}',
    page_icon='🚢',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# ==============================================================
#  CSS  --  WHITE THEME
# ==============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
html, body, .stApp, .stApp * { font-family: 'Montserrat', sans-serif !important; }
code, pre, [data-testid="stCode"], .stDataFrame td, .stDataFrame th { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: #ffffff !important; color: #1e293b !important; }
[data-testid="stHeader"] { background: #ffffff !important; border-bottom: 1px solid #e2e8f0; }

[data-testid="stMetric"] { background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; padding: 18px 20px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important; }
[data-testid="stMetric"]:hover { border-color: #3b82f6 !important; box-shadow: 0 4px 12px rgba(59,130,246,0.10) !important; }
[data-testid="stMetricLabel"] { font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.8px !important; color: #64748b !important; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-weight: 800 !important; font-size: 28px !important; color: #0f172a !important; }

.stTabs [data-baseweb="tab-list"] { gap: 0; background: #f8fafc; border-bottom: 2px solid #e2e8f0; }
.stTabs [data-baseweb="tab"] { font-family: 'Montserrat', sans-serif !important; font-weight: 600 !important; font-size: 13px !important; color: #64748b !important; padding: 14px 24px !important; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #1e3a5f !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #1e3a5f !important; }

[data-testid="stDataFrame"] { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; overflow: hidden !important; }

.stTextInput input, .stSelectbox [data-baseweb="select"], .stDateInput input { background: #f8fafc !important; border-color: #cbd5e1 !important; color: #1e293b !important; }
.stDownloadButton button { background: #1e3a5f !important; border: none !important; color: #ffffff !important; font-weight: 600 !important; border-radius: 8px !important; }
.stDownloadButton button:hover { background: #2a4f7a !important; }
.stButton button { border: 1px solid #cbd5e1 !important; color: #1e293b !important; font-weight: 600 !important; }
.stButton button:hover { border-color: #3b82f6 !important; color: #3b82f6 !important; }
hr { border-color: #e2e8f0 !important; }
.stMarkdown, .stCaption, p, span, label, h1, h2, h3, h4, h5, h6 { color: #1e293b !important; }

.synovia-banner { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1e4976 100%); border: none; border-radius: 14px; padding: 22px 28px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.synovia-banner .logos { display: flex; align-items: center; gap: 20px; }
.synovia-banner .logos img { height: 38px; border-radius: 4px; }
.synovia-banner .title { font-size: 18px; font-weight: 800; color: #ffffff; }
.synovia-banner .title .accent { color: #60a5fa; }
.synovia-banner .subtitle { font-size: 11px; color: #94a3b8; margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
.synovia-banner .info { text-align: right; }
.synovia-banner .env-badge { display: inline-block; padding: 3px 10px; border-radius: 5px; font-size: 10px; font-weight: 700; background: rgba(34,197,94,0.20); color: #4ade80; border: 1px solid rgba(34,197,94,0.30); text-transform: uppercase; margin-left: 8px; }
.synovia-banner .version-badge { display: inline-block; padding: 3px 10px; border-radius: 5px; font-size: 10px; font-weight: 600; background: rgba(96,165,250,0.20); color: #93c5fd; border: 1px solid rgba(96,165,250,0.30); font-family: 'JetBrains Mono', monospace; }

.status-tile { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 16px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.04); transition: all 0.2s; }
.status-tile:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-1px); }
.status-tile .icon { font-size: 26px; margin-bottom: 6px; }
.status-tile .label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px; }
.status-tile .value { font-size: 30px; font-weight: 800; font-family: 'JetBrains Mono', monospace; }

.synovia-footer { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 28px; margin-top: 32px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.synovia-footer img { height: 28px; opacity: 0.8; }
.synovia-footer .text { font-size: 10px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; text-align: right; }
</style>
""", unsafe_allow_html=True)


# ==============================================================
#  DATABASE
# ==============================================================
@st.cache_resource(ttl=300)
def get_connection_string():
    """Build connection string from env vars, with INI file fallback."""
    if DB_USER and DB_PASSWORD:
        # Cloud / env var mode
        return (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
    else:
        # Local dev fallback -- read from INI
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(INI_PATH)
        d = cfg['database']
        return (
            f"DRIVER={d['driver']};"
            f"SERVER={d['server']};"
            f"DATABASE={DB_NAME};"
            f"UID={d['user']};"
            f"PWD={d['password']};"
            f"Encrypt={d.get('encrypt', 'yes')};"
            f"TrustServerCertificate={d.get('trust_server_certificate', 'no')};"
        )

def run_query(sql):
    conn = pyodbc.connect(get_connection_string(), autocommit=False)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

@st.cache_data(ttl=60)
def load_headers():
    return run_query("""
        SELECT declaration_number, tss_status, movement_type,
            identity_no_transport, nationality_transport,
            arrival_date_time, arrival_date, arrival_port,
            place_of_loading, place_of_unloading,
            seal_number, route, carrier_eori, carrier_name,
            error_message, downloaded_at
        FROM PLE.EnsHeaders ORDER BY declaration_number
    """)

@st.cache_data(ttl=60)
def load_consignments():
    return run_query("""
        SELECT ens_declaration_number, declaration_number,
            tss_status, goods_description, trader_reference,
            transport_document_number, controlled_goods,
            consignor_eori, consignor_name, consignor_city,
            consignee_eori, consignee_name, consignee_city,
            importer_eori, importer_name,
            total_packages, gross_mass_kg,
            movement_reference_number, control_status,
            error_message, goods_item_count, synced_at
        FROM PLE.EnsConsignments
        ORDER BY ens_declaration_number, declaration_number
    """)

@st.cache_data(ttl=60)
def load_goods():
    return run_query("""
        SELECT goods_id, consignment_number, ens_declaration_number,
            goods_description, commodity_code,
            type_of_packages, number_of_packages,
            gross_mass_kg, net_mass_kg,
            country_of_origin, item_invoice_amount,
            procedure_code, controlled_goods, package_marks, synced_at
        FROM PLE.EnsGoodsItems ORDER BY consignment_number
    """)

@st.cache_data(ttl=30)
def load_api_log():
    return run_query("""
        SELECT TOP 5000 log_id, logged_at, declaration_type, call_type,
            reference, act_as_customer, url,
            http_status, response_status, response_message,
            duration_ms, error_detail, notes
        FROM PLE.ApiLog ORDER BY log_id DESC
    """)


# ==============================================================
#  HELPERS
# ==============================================================
def img_to_b64(path):
    p = Path(path)
    if p.exists():
        ext = p.suffix.lower().replace('.', '')
        mime = 'png' if ext == 'png' else 'jpeg'
        with open(p, 'rb') as f:
            return f'data:image/{mime};base64,{base64.b64encode(f.read()).decode()}'
    return ''

def download_filename(suffix, ext='csv'):
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    return f'{FULL_NAME}_{suffix}_{ts}.{ext}'

def get_status_config(status):
    return STATUS_CONFIG.get(status, DEFAULT_STATUS)

def render_status_tiles(status_counts, columns=5):
    cols = st.columns(columns)
    for i, (status, count) in enumerate(status_counts.items()):
        icon, colour, bg, border = get_status_config(status)
        with cols[i % columns]:
            st.markdown(f"""
            <div class="status-tile" style="border-left:4px solid {colour};background:{bg}">
                <div class="icon">{icon}</div>
                <div class="label" style="color:{colour}">{status}</div>
                <div class="value" style="color:{colour}">{count}</div>
            </div>
            """, unsafe_allow_html=True)

def render_header():
    fusion_b64 = img_to_b64(FUSION_LOGO)
    prime_b64  = img_to_b64(PRIMELINE_LOGO)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    fusion_img = f'<img src="{fusion_b64}" />' if fusion_b64 else ''
    prime_img  = f'<img src="{prime_b64}" />' if prime_b64 else ''
    env = 'RENDER' if os.environ.get('RENDER') else 'PROD'
    st.markdown(f"""
    <div class="synovia-banner">
        <div class="logos">{fusion_img}{prime_img}
            <div>
                <div class="title"><span class="accent">Synovia</span> Flow — TSS Sync Portal</div>
                <div class="subtitle">{PROJECT} · {COMPONENT} · <span class="version-badge">{VERSION_TAG}</span> · Primeline Express · PLE</div>
            </div>
        </div>
        <div class="info">
            <div style="font-size:12px;color:#cbd5e1;font-weight:600">{DB_NAME} <span class="env-badge">{env}</span></div>
            <div style="font-size:10px;color:#64748b;margin-top:4px;font-family:'JetBrains Mono',monospace">{now}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    synovia_b64 = img_to_b64(SYNOVIA_LOGO)
    synovia_img = f'<img src="{synovia_b64}" />' if synovia_b64 else ''
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    st.markdown(f"""
    <div class="synovia-footer">{synovia_img}
        <div class="text">{__product__} — {PROJECT}_{COMPONENT}_{VERSION_TAG} — Synovia Digital Ltd — {now}</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================
#  TAB: ENS HEADERS
# ==============================================================
def tab_ens_headers(df_headers, df_cons):
    cons_counts = df_cons.groupby('ens_declaration_number').size().reset_index(name='consignments')
    df = df_headers.merge(cons_counts, left_on='declaration_number', right_on='ens_declaration_number', how='left')
    df['consignments'] = df['consignments'].fillna(0).astype(int)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric('🚢 ENS Headers', len(df))
    mc2.metric('📦 Total Consignments', f"{int(df['consignments'].sum()):,}")
    mc3.metric('📋 Avg Cons / ENS', f"{df['consignments'].mean():.1f}" if len(df) else '0')

    st.markdown('##### Status Breakdown')
    render_status_tiles(df['tss_status'].value_counts().to_dict(), columns=min(df['tss_status'].nunique(), 5))
    st.divider()

    fc1, fc2, fc3 = st.columns([3, 2, 2])
    search = fc1.text_input('🔍 Search', placeholder='Declaration, carrier, port...', key='hdr_search')
    status_filter = fc2.selectbox('Status', ['All'] + sorted(df['tss_status'].dropna().unique().tolist()), key='hdr_status')
    sort_col = fc3.selectbox('Sort by', ['declaration_number','consignments','arrival_date_time','tss_status','carrier_name','arrival_port'], key='hdr_sort')

    filtered = df.copy()
    if status_filter != 'All': filtered = filtered[filtered['tss_status'] == status_filter]
    if search: filtered = filtered[filtered.apply(lambda r: search.lower() in ' '.join(str(v).lower() for v in r.values), axis=1)]
    filtered = filtered.sort_values(sort_col, ascending=True)

    st.caption(f'Showing {len(filtered)} of {len(df)} headers')
    st.download_button('📥 Export ENS Headers', filtered.to_csv(index=False).encode('utf-8'), file_name=download_filename('ENS_Headers'), mime='text/csv')
    st.dataframe(filtered[['declaration_number','tss_status','consignments','arrival_date_time','arrival_port','place_of_loading','place_of_unloading','carrier_name','route','identity_no_transport']].rename(columns={'declaration_number':'Declaration','tss_status':'Status','consignments':'📦 Cons','arrival_date_time':'Arrival','arrival_port':'Port','place_of_loading':'From','place_of_unloading':'To','carrier_name':'Carrier','route':'Route','identity_no_transport':'Vehicle'}), width="stretch", height=480, hide_index=True)

    st.divider()
    st.subheader('🔎 ENS Header Detail')
    selected = st.selectbox('Select ENS', [''] + filtered['declaration_number'].tolist(), key='ens_detail', format_func=lambda x: x if x else '— select —')
    if selected:
        hdr = df[df['declaration_number'] == selected].iloc[0]
        icon, colour, _, _ = get_status_config(hdr['tss_status'])
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric(f'{icon} Status', hdr['tss_status'] or '—')
        mc2.metric('📦 Consignments', int(hdr['consignments']))
        mc3.metric('📅 Arrival', str(hdr['arrival_date_time'] or '—'))
        mc4.metric('🗺️ Route', hdr['route'] or '—')
        with st.expander('📋 Full Header Details', expanded=True):
            d1, d2 = st.columns(2)
            d1.markdown(f"| Field | Value |\n|:------|:------|\n| **Declaration** | `{hdr['declaration_number']}` |\n| **Status** | {icon} {hdr['tss_status']} |\n| **Movement Type** | {hdr['movement_type']} |\n| **Arrival** | {hdr['arrival_date_time']} |\n| **Port** | {hdr['arrival_port']} |\n| **From** | {hdr['place_of_loading']} |\n| **To** | {hdr['place_of_unloading']} |")
            d2.markdown(f"| Field | Value |\n|:------|:------|\n| **Carrier** | {hdr['carrier_name']} |\n| **Carrier EORI** | `{hdr['carrier_eori']}` |\n| **Vehicle** | {hdr['identity_no_transport']} |\n| **Nationality** | {hdr['nationality_transport']} |\n| **Seal** | {hdr['seal_number']} |\n| **Route** | {hdr['route']} |\n| **Downloaded** | {hdr['downloaded_at']} |")
        if hdr['error_message']: st.error(f"❌ **Error:** {hdr['error_message']}")
        linked = df_cons[df_cons['ens_declaration_number'] == selected]
        if not linked.empty:
            st.markdown(f'#### 📦 Consignments ({len(linked)})')
            st.dataframe(linked[['declaration_number','tss_status','consignor_name','consignee_name','total_packages','gross_mass_kg','transport_document_number','movement_reference_number']].rename(columns={'declaration_number':'Consignment','tss_status':'Status','consignor_name':'Consignor','consignee_name':'Consignee','total_packages':'Packages','gross_mass_kg':'Mass (kg)','transport_document_number':'Transport Doc','movement_reference_number':'MRN'}), width="stretch", hide_index=True)
            st.download_button(f'📥 Export {selected} Consignments', linked.to_csv(index=False).encode('utf-8'), file_name=download_filename(f'Cons_{selected}'), mime='text/csv')
        else: st.info('No consignments synced yet.')


# ==============================================================
#  TAB: CONSIGNMENTS
# ==============================================================
def tab_consignments(df_cons, df_goods):
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric('📦 Consignments', f'{len(df_cons):,}')
    mc2.metric('📦 Total Packages', f"{int(df_cons['total_packages'].sum()):,}" if not df_cons.empty else '0')
    mc3.metric('⚖️ Total Mass (kg)', f"{df_cons['gross_mass_kg'].sum():,.0f}" if not df_cons.empty else '0')
    if not df_cons.empty:
        st.markdown('##### Status Breakdown')
        render_status_tiles(df_cons['tss_status'].value_counts().to_dict(), columns=min(df_cons['tss_status'].nunique(), 5))
    st.divider()

    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 2])
    search = fc1.text_input('🔍 Search', placeholder='DEC, consignor, consignee, MRN...', key='cons_search')
    ens_filter = fc2.selectbox('ENS Header', ['All'] + sorted(df_cons['ens_declaration_number'].dropna().unique().tolist()), key='cons_ens')
    status_filter = fc3.selectbox('Status', ['All'] + sorted(df_cons['tss_status'].dropna().unique().tolist()), key='cons_status')
    sort_col = fc4.selectbox('Sort by', ['declaration_number','ens_declaration_number','tss_status','consignor_name','total_packages','gross_mass_kg'], key='cons_sort')

    filtered = df_cons.copy()
    if ens_filter != 'All': filtered = filtered[filtered['ens_declaration_number'] == ens_filter]
    if status_filter != 'All': filtered = filtered[filtered['tss_status'] == status_filter]
    if search: filtered = filtered[filtered.apply(lambda r: search.lower() in ' '.join(str(v).lower() for v in r.values), axis=1)]
    filtered = filtered.sort_values(sort_col, ascending=True)

    st.caption(f'Showing {len(filtered)} of {len(df_cons)} consignments')
    st.download_button('📥 Export Consignments', filtered.to_csv(index=False).encode('utf-8'), file_name=download_filename('Consignments'), mime='text/csv')
    st.dataframe(filtered[['declaration_number','ens_declaration_number','tss_status','consignor_name','consignee_name','total_packages','gross_mass_kg','transport_document_number','movement_reference_number']].rename(columns={'declaration_number':'Consignment','ens_declaration_number':'ENS Header','tss_status':'Status','consignor_name':'Consignor','consignee_name':'Consignee','total_packages':'Packages','gross_mass_kg':'Mass (kg)','transport_document_number':'Transport Doc','movement_reference_number':'MRN'}), width="stretch", height=480, hide_index=True)

    st.divider()
    st.subheader('🔎 Consignment Detail')
    selected = st.selectbox('Select consignment', [''] + filtered['declaration_number'].tolist(), key='cons_detail', format_func=lambda x: x if x else '— select —')
    if selected:
        c = df_cons[df_cons['declaration_number'] == selected].iloc[0]
        icon, colour, _, _ = get_status_config(c['tss_status'])
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric(f'{icon} Status', c['tss_status'] or '—')
        mc2.metric('📦 Packages', int(c['total_packages'] or 0))
        mc3.metric('⚖️ Mass (kg)', f"{c['gross_mass_kg'] or 0:,.1f}")
        mc4.metric('📋 Goods Items', int(c['goods_item_count'] or 0))
        with st.expander('📋 Full Details', expanded=True):
            d1, d2 = st.columns(2)
            d1.markdown(f"| Field | Value |\n|:------|:------|\n| **Consignment** | `{c['declaration_number']}` |\n| **ENS Header** | `{c['ens_declaration_number']}` |\n| **Status** | {icon} {c['tss_status']} |\n| **Goods** | {c['goods_description']} |\n| **Transport Doc** | {c['transport_document_number']} |\n| **Trader Ref** | {c['trader_reference']} |\n| **MRN** | {c['movement_reference_number']} |")
            d2.markdown(f"| Field | Value |\n|:------|:------|\n| **Consignor** | {c['consignor_name']} |\n| **Consignor EORI** | `{c['consignor_eori']}` |\n| **Consignee** | {c['consignee_name']} |\n| **Consignee EORI** | `{c['consignee_eori']}` |\n| **Importer** | {c['importer_name']} |\n| **Importer EORI** | `{c['importer_eori']}` |\n| **Control** | {c['control_status']} |")
        if c['error_message']: st.error(f"❌ **Error:** {c['error_message']}")
        linked = df_goods[df_goods['consignment_number'] == selected]
        if not linked.empty:
            st.markdown(f'#### 📋 Goods Items ({len(linked)})')
            st.dataframe(linked[['commodity_code','goods_description','number_of_packages','gross_mass_kg','country_of_origin','item_invoice_amount','procedure_code']].rename(columns={'commodity_code':'Commodity','goods_description':'Description','number_of_packages':'Packages','gross_mass_kg':'Mass (kg)','country_of_origin':'Origin','item_invoice_amount':'Value','procedure_code':'Procedure'}), width="stretch", hide_index=True)
            st.download_button(f'📥 Export {selected} Goods', linked.to_csv(index=False).encode('utf-8'), file_name=download_filename(f'Goods_{selected}'), mime='text/csv')


# ==============================================================
#  TAB: GOODS
# ==============================================================
def tab_goods(df_goods):
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric('📋 Goods Items', f'{len(df_goods):,}')
    if not df_goods.empty:
        mc2.metric('🏷️ Commodities', df_goods['commodity_code'].nunique())
        mc3.metric('⚖️ Mass (kg)', f"{df_goods['gross_mass_kg'].sum():,.0f}")
        mc4.metric('📦 Packages', f"{int(df_goods['number_of_packages'].sum()):,}")
    st.divider()

    fc1, fc2, fc3 = st.columns([3, 2, 2])
    search = fc1.text_input('🔍 Search', placeholder='Commodity, description...', key='goods_search')
    cons_filter = fc2.selectbox('Consignment', ['All'] + sorted(df_goods['consignment_number'].dropna().unique().tolist()[:200]), key='goods_cons')
    sort_col = fc3.selectbox('Sort by', ['consignment_number','commodity_code','goods_description','gross_mass_kg','number_of_packages'], key='goods_sort')

    filtered = df_goods.copy()
    if cons_filter != 'All': filtered = filtered[filtered['consignment_number'] == cons_filter]
    if search: filtered = filtered[filtered.apply(lambda r: search.lower() in ' '.join(str(v).lower() for v in r.values), axis=1)]
    filtered = filtered.sort_values(sort_col, ascending=True)

    st.caption(f'Showing {len(filtered)} of {len(df_goods)}')
    st.download_button('📥 Export Goods', filtered.to_csv(index=False).encode('utf-8'), file_name=download_filename('Goods_Items'), mime='text/csv')
    st.dataframe(filtered[['consignment_number','commodity_code','goods_description','number_of_packages','gross_mass_kg','net_mass_kg','country_of_origin','item_invoice_amount','procedure_code']].rename(columns={'consignment_number':'Consignment','commodity_code':'Commodity','goods_description':'Description','number_of_packages':'Packages','gross_mass_kg':'Mass (kg)','net_mass_kg':'Net (kg)','country_of_origin':'Origin','item_invoice_amount':'Value','procedure_code':'Procedure'}), width="stretch", height=480, hide_index=True)

    if not filtered.empty:
        st.divider()
        st.subheader('📊 Commodity Breakdown')
        comm = filtered.groupby('commodity_code').agg(items=('commodity_code','size'), total_kg=('gross_mass_kg','sum'), total_pkgs=('number_of_packages','sum')).reset_index().sort_values('items', ascending=False).head(20)
        st.dataframe(comm.rename(columns={'commodity_code':'Commodity','items':'Items','total_kg':'Total kg','total_pkgs':'Packages'}), width="stretch", hide_index=True)


# ==============================================================
#  TAB: API LOG
# ==============================================================
def tab_api_log(df_log):
    if df_log.empty: st.info('No API log entries.'); return
    ok = (df_log['response_status'] == 'OK').sum()
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric('📡 API Calls', f'{len(df_log):,}')
    mc2.metric('✅ Successful', f'{ok:,}')
    mc3.metric('❌ Failed', f'{len(df_log)-ok:,}')
    mc4.metric('⏱️ Avg ms', f'{df_log["duration_ms"].mean():.0f}')
    st.divider()

    fc1, fc2, fc3, fc4, fc5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    search = fc1.text_input('🔍 Search', placeholder='Reference, url...', key='log_search')
    result_filter = fc2.selectbox('Result', ['All','OK','FAIL'], key='log_result')
    type_filter = fc3.selectbox('Type', ['All'] + sorted(df_log['declaration_type'].dropna().unique().tolist()), key='log_type')
    if df_log['logged_at'].notna().any():
        min_d = pd.to_datetime(df_log['logged_at']).min().date()
        max_d = pd.to_datetime(df_log['logged_at']).max().date()
    else: min_d = max_d = datetime.now().date()
    date_from = fc4.date_input('From', min_d, key='log_from')
    date_to = fc5.date_input('To', max_d, key='log_to')

    filtered = df_log.copy()
    if result_filter != 'All': filtered = filtered[filtered['response_status'] == result_filter]
    if type_filter != 'All': filtered = filtered[filtered['declaration_type'] == type_filter]
    if search: filtered = filtered[filtered.apply(lambda r: search.lower() in ' '.join(str(v).lower() for v in r.values), axis=1)]
    if filtered['logged_at'].notna().any():
        ld = pd.to_datetime(filtered['logged_at']).dt.date
        filtered = filtered[(ld >= date_from) & (ld <= date_to)]

    st.caption(f'Showing {len(filtered)} of {len(df_log)}')
    st.download_button('📥 Export API Log', filtered.to_csv(index=False).encode('utf-8'), file_name=download_filename('API_Log'), mime='text/csv')
    st.dataframe(filtered[['log_id','logged_at','declaration_type','reference','url','http_status','response_status','duration_ms','notes']].rename(columns={'log_id':'#','logged_at':'Timestamp','declaration_type':'Type','reference':'Reference','url':'Endpoint','http_status':'HTTP','response_status':'Result','duration_ms':'ms','notes':'Notes'}), width="stretch", height=480, hide_index=True)

    st.divider()
    bc1, bc2 = st.columns(2)
    with bc1:
        st.subheader('📊 Calls by Type')
        ta = filtered.groupby('declaration_type').agg(calls=('log_id','size'), ok=('response_status', lambda x: (x=='OK').sum()), avg_ms=('duration_ms','mean')).reset_index().sort_values('calls', ascending=False)
        ta['fail'] = ta['calls'] - ta['ok']; ta['avg_ms'] = ta['avg_ms'].round(0)
        st.dataframe(ta.rename(columns={'declaration_type':'Type','calls':'Calls','ok':'✅','fail':'❌','avg_ms':'Avg ms'}), width="stretch", hide_index=True)
    with bc2:
        st.subheader('📊 HTTP Breakdown')
        st.dataframe(filtered.groupby('http_status').size().reset_index(name='Count').sort_values('Count', ascending=False).rename(columns={'http_status':'HTTP'}), width="stretch", hide_index=True)


# ==============================================================
#  MAIN
# ==============================================================
def main():
    render_header()
    with st.spinner('Connecting to database...'):
        try:
            df_h = load_headers()
            df_c = load_consignments()
            df_g = load_goods()
            df_l = load_api_log()
        except Exception as e:
            st.error(f'**Database connection failed:** {e}')
            st.info('Set environment variables: `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`')
            return

    rc1, rc2 = st.columns([6, 1])
    with rc2:
        if st.button('🔄 Refresh', use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    t1, t2, t3, t4 = st.tabs([f'🚢 ENS Headers ({len(df_h)})', f'📦 Consignments ({len(df_c):,})', f'📋 Goods Items ({len(df_g):,})', f'📡 API Log ({len(df_l):,})'])
    with t1: tab_ens_headers(df_h, df_c)
    with t2: tab_consignments(df_c, df_g)
    with t3: tab_goods(df_g)
    with t4: tab_api_log(df_l)
    render_footer()

if __name__ == '__main__':
    main()
