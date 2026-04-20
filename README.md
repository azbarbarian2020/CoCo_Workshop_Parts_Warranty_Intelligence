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
- [Snow CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) installed and configured (for Option B file upload)

## Quick Start

### Phase 1: Create Infrastructure

Run **Sections 1-2** of [`sql/00_setup.sql`](sql/00_setup.sql) in a Snowflake worksheet. This creates the database, warehouse, schemas, and stages.

### Phase 2: Upload Files

Upload the CSV data files and PDF manuals to the stages created in Phase 1.

**Option A — Snowsight UI (no CLI required)**

1. Download the 3 CSV files from the [`data/`](data/) folder and the 5 PDF files from the [`docs/`](docs/) folder in this repo
2. In Snowsight, navigate to **Data** > **Databases** > **COCO_WORKSHOP** > **BRONZE**
3. Upload the 3 CSVs to the `DATA_STAGE` stage
4. Upload the 5 PDFs to the `DOCS` stage

**Option B — Snow CLI (from cloned repo)**

```bash
snow stage copy data/*.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
snow stage copy docs/PM_*.pdf @COCO_WORKSHOP.BRONZE.DOCS --overwrite
```

### Phase 3: Load Bronze Tables

Run **Sections 3-5** of [`sql/00_setup.sql`](sql/00_setup.sql) to create the Bronze tables, load the CSVs, and verify row counts.

### Run the Workshop

Open CoCo and follow the prompts in [`WORKSHOP_PROMPT_GUIDE.md`](WORKSHOP_PROMPT_GUIDE.md).

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
│   └── warranty_claims.csv      # 500 rows — free-text complaints and tech notes
├── docs/                        # 5 PDF parts service manuals
│   ├── PM_TC-5000_Turbocharger_Assembly.pdf
│   ├── PM_TCM-3200_Transmission_Control_Module.pdf
│   ├── PM_EXM-4100_Exhaust_Manifold_Assembly.pdf
│   ├── PM_ACM-2800_Air_Compressor_Assembly.pdf
│   └── PM_SGB-6500_Steering_Gear_Box.pdf
└── scripts/                     # Data generation scripts (optional, for regeneration)
    ├── generate_parts_data.py
    ├── generate_warranty_claims.py
    └── generate_part_manuals.py
```

## Regenerating Data (Optional)

If you need to regenerate the sample data or PDFs:

```bash
pip install fpdf2
python scripts/generate_parts_data.py
python scripts/generate_warranty_claims.py
python scripts/generate_part_manuals.py
```
