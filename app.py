# app.py
import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(
    page_title="VAL ROLLERS INC. - DLA Command Center",
    layout="wide"
)

# Initialize DuckDB in-memory database and populate tables
@st.cache_resource
def init_db():
    con = duckdb.connect(database=":memory:")
    
    con.execute("""
        CREATE TABLE IF NOT EXISTS contract_archive (
            contract_id VARCHAR PRIMARY KEY,
            part_number VARCHAR,
            contract_title VARCHAR,
            start_date VARCHAR,
            end_date VARCHAR,
            total_value DECIMAL,
            status VARCHAR
        );
    """)
    
    res = con.execute("SELECT COUNT(*) FROM contract_archive").fetchone()[0]
    if res == 0:
        con.execute("""
            INSERT INTO contract_archive VALUES 
            ('SPE4A526V1114', 'VAL3900', 'DLA Aviation Titanium Fastener & Roller Lot', '2026-05-28', '2026-11-28', 1474.00, 'ACTIVE'),
            ('SPE4A526V0815', 'AM3885-G', 'Air Force Ground Support Roller Lot (SAM.gov)', '2026-05-13', '2026-11-13', 70488.00, 'ACTIVE'),
            ('SPE4A626PB076', 'LG-9021', 'Marine Corps Amphibious Drive Shaft', '2026-01-06', '2027-01-06', 24321.00, 'COMPLETED'),
            ('SPE4A525V2130', 'VAL4000', 'Air Force Ground Support Casters', '2025-07-25', '2026-01-25', 16619.11, 'COMPLETED'),
            ('SPE4A125V0332', 'VAL3900', 'Navy Phalanx CIWS Feed Roller', '2025-03-31', '2025-09-31', 31960.00, 'COMPLETED');
        """)

    con.execute("""
        CREATE OR REPLACE TABLE nsn_registry AS 
        SELECT * FROM (VALUES 
            ('4920-00-782-3806', 'VAL3900 / 21C2201-093', 'Roller, Adapter Assembly', 'F/A-18 Engine Tooling / DLA Aviation', 'MIL-Q-9858 / ISO 9001:2015'),
            ('4920-01-080-4020', 'AM3885-G', 'Roller, Maintenance Support', 'Ground Support Equipment', 'MIL-STD-45662A Calibration'),
            ('4920-00-653-8943', 'VAL4000', 'Roller, Engine Test Interface', 'Test Cell Equipment', 'AS9120B Traceable'),
            ('1620-01-234-5511', 'LG-9021', 'Actuator Assembly, Landing Gear', 'F-35 Hydraulic Subsystem', 'AS9100D Certified'),
            ('2840-01-441-9082', 'TF-34-TR', 'Turbine Rotor Blade Interface', 'A-10 Thunderbolt Propulsion', 'MIL-E-5002 Plating Standard')
        ) AS t(nsn, cross_parts, item_name, application_platform, quality_standard);
    """)

    con.execute("""
        CREATE OR REPLACE TABLE dibbs_solicitations AS 
        SELECT * FROM (VALUES 
            ('RFQ-DLA-2026-9901', '4920-00-782-3806', 'VAL3900', 'Roller, Adapter Urgent Open Solicitation', 15, '2026-09-25', 'OPEN_BIDDING', 24850.00, 1656.66, 670.00, 986.66, 14800.00),
            ('RFQ-DLA-2026-9902', '4920-00-653-8943', 'VAL4000', 'Engine Test Roller Replacement Batch', 50, '2026-09-30', 'OPEN_BIDDING', 68400.00, 1368.00, 310.00, 1058.00, 52900.00),
            ('RFQ-DLA-2026-8814', '4920-01-080-4020', 'AM3885-G', 'Maintenance Support Roller Set-Aside', 25, '2026-10-05', 'OPEN_BIDDING', 34750.00, 1390.00, 450.00, 940.00, 23500.00),
            ('RFQ-DLA-2026-7730', '1620-01-234-5511', 'LG-9021', 'Landing Gear Actuator Overhaul Batch', 10, '2026-10-12', 'OPEN_BIDDING', 41200.00, 4120.00, 1250.00, 2870.00, 28700.00),
            ('RFQ-DLA-2026-6219', '2840-01-441-9082', 'TF-34-TR', 'Turbine Rotor Blade Interface Stock', 100, '2026-10-20', 'OPEN_BIDDING', 52000.00, 520.00, 189.00, 331.00, 33100.00)
        ) AS t(solicitation_id, nsn, part_number, description, target_quantity, response_deadline, status, estimated_contract_value, current_unit_bid, unit_material_cost, unit_profit, total_projected_profit);
    """)

    con.execute("""
        CREATE OR REPLACE TABLE supplier_quotes AS 
        SELECT * FROM (VALUES 
            ('SUP-01', 'AeroMetal Stock Co.', '4920-00-782-3806', 'Alloy Steel Bar Stock (DFARS Compliant)', 450.00, '2026-06-01', 'ACTIVE'),
            ('SUP-02', 'Apex Precision Heat Treat', '4920-00-782-3806', 'Vacuum Heat Treatment & Hardening Batch', 220.00, '2026-06-05', 'ACTIVE'),
            ('SUP-03', 'Summit Coating Tech', '4920-00-653-8943', 'Cadmium Plating / Surface Finish', 310.00, '2026-06-10', 'ACTIVE'),
            ('SUP-04', 'Vanguard Aerospace Alloys', '1620-01-234-5511', 'High-Strength Titanium Forging Stock', 1250.00, '2026-06-15', 'ACTIVE'),
            ('SUP-05', 'Titan Thermal Processors', '2840-01-441-9082', 'Superalloy Thermal Barrier Coating', 189.00, '2026-06-18', 'ACTIVE')
        ) AS t(supplier_id, supplier_name, nsn, material_description, quote_cost, quote_date, status);
    """)
    return con

db_con = init_db()

# Initialize Session State for Inspection Telemetry
if 'selected_record' not in st.session_state:
    st.session_state['selected_record'] = None

# Custom styling for dark theme and badges
st.markdown("""
<style>
    .stApp {
        background-color: #020617;
        color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("## VAL ROLLERS INC.")
    st.markdown(
        '<span style="background-color: #1e1b4b; color: #a5b4fc; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid #312e81; font-weight: bold;">CAGE: 0B039</span> '
        '<span style="background-color: #1e1b4b; color: #a5b4fc; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid #312e81; font-weight: bold;">UEI: TRH4N9X474F6</span>',
        unsafe_allow_html=True
    )
    st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-top: 5px;'>Defense Logistics Agency (DLA) Ontology Command & Pricing Center</p>", unsafe_allow_html=True)

with header_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Export DLA Batch Bid CSV", type="primary", use_container_width=True):
        st.success("Batch bid CSV package generated successfully for DLA submission compliance.")
    st.markdown('<div style="text-align: right;"><span style="background-color: #022c22; color: #34d399; font-size: 11px; padding: 4px 10px; border-radius: 4px; border: 1px solid #065f46; display: inline-block;">SAM.gov Live Sync Active</span></div>', unsafe_allow_html=True)

st.markdown("---")

# Navigation Tabs
tab_choice = st.radio(
    "Navigation", 
    ["Active DIBBS Solicitations", "Contract Archive & Analytics", "NSN Registry", "Supplier Quotations"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# Main Grid Layout (Left: Records Container, Right: Intelligence Panel)
col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    if tab_choice == "Active DIBBS Solicitations":
        st.markdown("<h3 style='font-size: 14px; color: #818cf8; font-weight: bold; letter-spacing: 0.05em;'>ACTIVE DLA DIBBS OPEN SOLICITATIONS</h3>", unsafe_allow_html=True)
        query = "SELECT * FROM dibbs_solicitations ORDER BY response_deadline ASC"
        df = db_con.execute(query).fetchdf()
        st.markdown(f"<span style='background-color: #1e293b; color: #cbd5e1; font-size: 11px; padding: 2px 8px; border-radius: 10px;'>{len(df)} records</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #0f172a; border: 1px solid #1e293b; padding: 14px; border-radius: 8px; margin-bottom: 10px;">
                    <span style="background-color: #451a03; color: #fbbf24; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; border: 1px solid #78350f;">OPEN RFQ</span>
                    <h4 style="color: white; margin: 6px 0 4px 0; font-size: 14px;">{row['description']}</h4>
                    <p style="color: #94a3b8; font-size: 11px; margin: 0; line-height: 1.5;">
                        RFQ: {row['solicitation_id']} • Part: <span style="color: #818cf8; font-family: monospace;">{row['part_number']}</span> • Qty: {row['target_quantity']}<br>
                        Current Bid: <span style="color: #34d399; font-weight: bold;">${row['current_unit_bid']:,.2f}</span>/unit | 
                        Mat. Cost: <span style="color: #fbbf24; font-weight: bold;">${row['unit_material_cost']:,.2f}</span> | 
                        Profit: <span style="color: #22d3ee; font-weight: bold;">${row['unit_profit']:,.2f}/unit (${row['total_projected_profit']:,.2f} total)</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Analyze", key=f"btn_dibbs_{row['solicitation_id']}"):
                    st.session_state['selected_record'] = row.to_dict()

    elif tab_choice == "Contract Archive & Analytics":
        st.markdown("<h3 style='font-size: 14px; color: #818cf8; font-weight: bold; letter-spacing: 0.05em;'>CONTRACT ARCHIVE & ANALYTICS</h3>", unsafe_allow_html=True)
        query = "SELECT * FROM contract_archive ORDER BY start_date DESC"
        df = db_con.execute(query).fetchdf()
        st.markdown(f"<span style='background-color: #1e293b; color: #cbd5e1; font-size: 11px; padding: 2px 8px; border-radius: 10px;'>{len(df)} records</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for _, row in df.iterrows():
            badge_bg = "#064e3b" if row['status'] == 'ACTIVE' else "#1e293b"
            badge_fg = "#34d399" if row['status'] == 'ACTIVE' else "#94a3b8"
            with st.container():
                st.markdown(f"""
                <div style="background-color: #0f172a; border: 1px solid #1e293b; padding: 14px; border-radius: 8px; margin-bottom: 10px;">
                    <span style="background-color: {badge_bg}; color: {badge_fg}; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">{row['status']}</span>
                    <span style="font-family: monospace; font-size: 10px; background-color: #312e81; color: #a5b4fc; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">Part: {row['part_number']}</span>
                    <h4 style="color: white; margin: 6px 0 4px 0; font-size: 14px;">{row['contract_title']}</h4>
                    <p style="color: #94a3b8; font-size: 11px; margin: 0;">
                        Contract: {row['contract_id']} • Start: {row['start_date']} • Value: <span style="color: #34d399; font-weight: bold;">${row['total_value']:,.2f}</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Review", key=f"btn_contract_{row['contract_id']}"):
                    st.session_state['selected_record'] = row.to_dict()

    elif tab_choice == "NSN Registry":
        st.markdown("<h3 style='font-size: 14px; color: #818cf8; font-weight: bold; letter-spacing: 0.05em;'>NATO STOCK NUMBER (NSN) REGISTRY</h3>", unsafe_allow_html=True)
        query = "SELECT * FROM nsn_registry"
        df = db_con.execute(query).fetchdf()
        st.markdown(f"<span style='background-color: #1e293b; color: #cbd5e1; font-size: 11px; padding: 2px 8px; border-radius: 10px;'>{len(df)} records</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #0f172a; border: 1px solid #1e293b; padding: 14px; border-radius: 8px; margin-bottom: 10px;">
                    <span style="background-color: #3b0764; color: #d8b4fe; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">NSN ITEM</span>
                    <h4 style="color: white; margin: 6px 0 4px 0; font-size: 14px;">{row['item_name']}</h4>
                    <p style="color: #94a3b8; font-size: 11px; margin: 0;">
                        NSN: <span style="color: #818cf8; font-family: monospace;">{row['nsn']}</span> • Parts: {row['cross_parts']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Inspect", key=f"btn_nsn_{row['nsn']}"):
                    st.session_state['selected_record'] = row.to_dict()

    elif tab_choice == "Supplier Quotations":
        st.markdown("<h3 style='font-size: 14px; color: #818cf8; font-weight: bold; letter-spacing: 0.05em;'>SUBCONTRACTOR & SUPPLIER QUOTATION TRACKER</h3>", unsafe_allow_html=True)
        query = "SELECT * FROM supplier_quotes ORDER BY quote_date ASC"
        df = db_con.execute(query).fetchdf()
        st.markdown(f"<span style='background-color: #1e293b; color: #cbd5e1; font-size: 11px; padding: 2px 8px; border-radius: 10px;'>{len(df)} records</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #0f172a; border: 1px solid #1e293b; padding: 14px; border-radius: 8px; margin-bottom: 10px;">
                    <span style="background-color: #064e3b; color: #34d399; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">SUPPLIER QUOTE</span>
                    <h4 style="color: white; margin: 6px 0 4px 0; font-size: 14px;">{row['material_description']}</h4>
                    <p style="color: #94a3b8; font-size: 11px; margin: 0;">
                        Vendor: {row['supplier_name']} • Cost: <span style="color: #34d399; font-weight: bold;">${row['quote_cost']:,.2f}</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View", key=f"btn_supplier_{row['supplier_id']}"):
                    st.session_state['selected_record'] = row.to_dict()

with col_right:
    st.markdown("<h3 style='font-size: 13px; color: #cbd5e1; font-weight: bold; letter-spacing: 0.05em;'>INTELLIGENCE & MARGIN TRACKING</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 11px; color: #64748b; margin-top: -5px;'>Computed unit economics and automated bid baselines.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state['selected_record'] is not None:
        st.markdown("""
        <div style="border-bottom: 1px solid #1e293b; padding-bottom: 6px; margin-bottom: 10px;">
            <span style="font-size: 11px; color: #818cf8; font-weight: bold; text-transform: uppercase;">Inspection Telemetry</span>
        </div>
        """, unsafe_allow_html=True)
        
        for key, val in st.session_state['selected_record'].items():
            formatted_key = key.replace('_', ' ').title()
            st.markdown(f"<div style='margin-bottom: 8px;'><strong style='color: #94a3b8; font-size: 11px;'>{formatted_key}:</strong><br><span style='color: #f1f5f9; font-size: 12px;'>{val}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="border: 1px dashed #1e293b; border-radius: 8px; padding: 40px 20px; text-align: center; color: #64748b;">
            <p style="font-weight: 500; color: #cbd5e1; font-size: 13px; margin: 0;">No record selected</p>
            <p style="font-size: 11px; color: #64748b; margin-top: 5px;">Select an item from the left panel to inspect economic data.</p>
        </div>
        """, unsafe_allow_html=True)
