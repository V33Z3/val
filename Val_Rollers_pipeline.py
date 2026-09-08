import os
import duckdb
import pandas as pd

os.makedirs("data", exist_ok=True)

# 1. DLA Federal Contracts (Government Orders)
contracts_df = pd.DataFrame([
    {"contract_id": "SPE4A6-21-V-551V", "nsn": "1730-01-234-5678", "part_number": "AM3800", "description": "Adapter, Double Roller", "quantity": 58, "deadline": "2026-04-15", "status": "IN_PRODUCTION"},
    {"contract_id": "SPE4A6-23-V-8362", "nsn": "4920-01-890-1234", "part_number": "AM3885-G", "description": "Uplift Attachment", "quantity": 29, "deadline": "2026-03-30", "status": "QA_PENDING"}
])
contracts_df.to_csv("data/dla_contracts.csv", index=False)

# 2. Shop Floor & CNC Work Orders
jobs_df = pd.DataFrame([
    {"job_id": "JOB-101", "part_number": "AM3800", "machine": "CNC Mill 01", "operator": "J. Williams", "material_lot": "AL-7075-992", "status": "MACHINING"},
    {"job_id": "JOB-102", "part_number": "AM3885-G", "machine": "Lathe 03", "operator": "M. Davis", "material_lot": "STL-4340-112", "status": "INSPECTION"}
])
jobs_df.to_csv("data/shop_jobs.csv", index=False)

# 3. Quality Assurance & Inspection Logs (MIL-Q-9858 compliance)
qa_df = pd.DataFrame([
    {"inspection_id": "QA-501", "job_id": "JOB-101", "tolerance_check": "PASS", "laser_tir_inches": 0.0008, "certified": True},
    {"inspection_id": "QA-502", "job_id": "JOB-102", "tolerance_check": "PENDING", "laser_tir_inches": None, "certified": False}
])
qa_df.to_csv("data/quality_logs.csv", index=False)

def run_val_rollers_pipeline():
    con = duckdb.connect("ontology.duckdb")
    print("Building Val Rollers Inc. Defense Manufacturing Ontology...")

    # Load raw data into staging
    con.execute("CREATE OR REPLACE TABLE raw_contracts AS SELECT * FROM 'data/dla_contracts.csv';")
    con.execute("CREATE OR REPLACE TABLE raw_jobs AS SELECT * FROM 'data/shop_jobs.csv';")
    con.execute("CREATE OR REPLACE TABLE raw_qa AS SELECT * FROM 'data/quality_logs.csv';")

    # Map to Ontology Object Views
    con.execute("""
        CREATE OR REPLACE VIEW object_contracts AS 
        SELECT contract_id AS id, description || ' (' || part_number || ')' AS title, nsn, quantity, deadline, status, 'Contract' AS object_type FROM raw_contracts;
    """)
    con.execute("""
        CREATE OR REPLACE VIEW object_jobs AS 
        SELECT job_id AS id, 'Job for ' || part_number || ' on ' || machine AS title, machine, operator, material_lot, status, 'ShopJob' AS object_type FROM raw_jobs;
    """)
    con.execute("""
        CREATE OR REPLACE VIEW object_qa AS 
        SELECT inspection_id AS id, 'Inspection ' || inspection_id || ' [' || tolerance_check || ']' AS title, job_id, tolerance_check, laser_tir_inches, certified, 'QualityLog' AS object_type FROM raw_qa;
    """)

    # Connect DLA Contracts to Shop Floor Jobs and QA Inspections
    con.execute("""
        CREATE OR REPLACE VIEW link_val_rollers_network AS
        SELECT j.job_id AS source_id, 'ShopJob' AS source_type, c.contract_id AS target_id, 'Contract' AS target_type, 'FULFILLS_CONTRACT' AS relationship 
        FROM raw_jobs j
        JOIN raw_contracts c ON j.part_number = c.part_number
        UNION ALL
        SELECT q.inspection_id AS source_id, 'QualityLog' AS source_type, q.job_id AS target_id, 'ShopJob' AS target_type, 'INSPECTED_BY' AS relationship 
        FROM raw_qa q;
    """)

    print("Val Rollers ontology compiled successfully.")
    con.close()

if __name__ == "__main__":
    run_val_rollers_pipeline()