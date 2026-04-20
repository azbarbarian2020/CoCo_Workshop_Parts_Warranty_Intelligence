# CoCo Workshop: Parts Warranty Intelligence

A ~30-minute hands-on workshop that builds an AI-powered warranty analytics agent from scratch using **Cortex Code (CoCo)** and natural language prompts. No code is written manually — every table, transformation, semantic view, search service, and agent is created by prompting CoCo.

## What You Build

```
Bronze (raw CSVs + PDFs)
  → Silver (AI-enriched: summaries, categories, classifications)
    → Gold (analytics-ready: clean tables, semantic view, search service)
      → Cortex Agent (natural language Q&A over structured data + PDF manuals)
```

Three data stories are embedded for the agent to discover:
- **Bad Batch**: One batch of VGT Actuators from Precision Dynamics fails at 5.7% vs <1.3% baseline
- **Bad Supplier**: All NovaTech Main PCB batches fail at 3.07% vs near-zero for other suppliers
- **Design Problem**: Piston & Cylinder Kits fail at similar rates (~1%) across all three suppliers

## Prerequisites

- Snowflake account with `ACCOUNTADMIN` role (or equivalent)
- [Cortex Code (CoCo)](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) access
- [Snow CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) installed and configured
- A warehouse (the guide uses `SNOW_INTELLIGENCE_DEMO_WH` — change to yours)

## Quick Start

### 1. Create infrastructure

Run **Sections 1-2** of `sql/00_setup.sql` in Snowflake to create the database, schemas, and stages:

```sql
-- Run in Snowflake worksheet or Snow CLI
CREATE DATABASE IF NOT EXISTS COCO_WORKSHOP;
USE DATABASE COCO_WORKSHOP;
CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS GOLD;
CREATE STAGE IF NOT EXISTS BRONZE.DATA_STAGE;
CREATE STAGE IF NOT EXISTS BRONZE.DOCS
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

### 2. Upload files

```bash
snow stage copy data/suppliers.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
snow stage copy data/parts.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
snow stage copy data/warranty_claims.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
snow stage copy data/docs/PM_*.pdf @COCO_WORKSHOP.BRONZE.DOCS --overwrite
```

### 3. Load Bronze tables

Run **Sections 3-5** of `sql/00_setup.sql` to create and load the Bronze tables.

### 4. Run the workshop

Open CoCo and follow the prompts in [WORKSHOP_PROMPT_GUIDE.md](WORKSHOP_PROMPT_GUIDE.md).

## Reset Between Runs

Run `sql/99_teardown.sql` to drop everything except Bronze tables and stages, then re-run the workshop from Step 1.

## Repository Structure

```
├── README.md                    # This file
├── WORKSHOP_PROMPT_GUIDE.md     # Step-by-step prompt guide and talk track
├── sql/
│   ├── 00_setup.sql             # Create DB, schemas, stages, load Bronze
│   └── 99_teardown.sql          # Reset for re-demo (preserves Bronze)
├── data/
│   ├── suppliers.csv            # 12 rows — supplier master data (with quality issues)
│   ├── parts.csv                # 25,000 rows — 5 part types with JSON BOM
│   ├── warranty_claims.csv      # 500 rows — free-text complaints and tech notes
│   └── docs/                    # 5 PDF parts service manuals
│       ├── PM_TC-5000_Turbocharger_Assembly.pdf
│       ├── PM_TCM-3200_Transmission_Control_Module.pdf
│       ├── PM_EXM-4100_Exhaust_Manifold_Assembly.pdf
│       ├── PM_ACM-2800_Air_Compressor_Assembly.pdf
│       └── PM_SGB-6500_Steering_Gear_Box.pdf
└── scripts/                     # Data generation scripts (optional, for regeneration)
    ├── generate_parts_data.py
    ├── generate_warranty_claims.py
    └── generate_part_manuals.py
```

## Warehouse Note

The workshop guide references `SNOW_INTELLIGENCE_DEMO_WH`. Replace with your warehouse name in CoCo prompts if needed.

## Regenerating Data (Optional)

If you need to regenerate the sample data or PDFs:

```bash
pip install fpdf2
python scripts/generate_parts_data.py
python scripts/generate_warranty_claims.py
python scripts/generate_part_manuals.py
```
