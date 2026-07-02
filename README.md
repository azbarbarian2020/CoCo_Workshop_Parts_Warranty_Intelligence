# CoCo Workshop: Parts Warranty Intelligence

> **Multi-User?** If running this workshop with multiple participants on the same Snowflake account, use [`sql/00_setup_multiuser.sql`](sql/00_setup_multiuser.sql) and [`WORKSHOP_PROMPT_GUIDE_MULTIUSER.md`](WORKSHOP_PROMPT_GUIDE_MULTIUSER.md) instead. These versions prefix each user's database and warehouse with their username so participants don't collide.

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

## Quick Start

### Step 1: Run the Setup Script

Run [`sql/00_setup.sql`](sql/00_setup.sql) in a Snowflake worksheet. The script is **fully self-contained** — it automatically:

1. Creates the database (`COCO_WORKSHOP`), warehouse, and schemas (Bronze/Silver/Gold)
2. Creates a Git Repository integration pointing to this repo
3. Copies the 3 CSV data files and 5 PDF manuals from GitHub directly into Snowflake stages
4. Creates Bronze tables and loads the CSVs
5. Verifies row counts and docs stage contents

No manual file uploads or Snow CLI required.

### Step 2: Run the Workshop

Open CoCo and follow the prompts in [`WORKSHOP_PROMPT_GUIDE.md`](WORKSHOP_PROMPT_GUIDE.md).

## Reset Between Runs

Run `sql/99_teardown.sql` to drop everything except Bronze tables and stages, then re-run the workshop from Step 1.

## Repository Structure

```
├── README.md                    # This file
├── WORKSHOP_PROMPT_GUIDE.md     # Step-by-step prompt guide and talk track
├── sql/
│   ├── 00_setup.sql             # Create DB, schemas, stages, load Bronze (self-contained)
│   └── 99_teardown.sql          # Reset for re-demo (preserves Bronze)
├── data/
│   ├── suppliers.csv            # 12 rows — supplier master data (with quality issues)
│   ├── parts.csv                # 25,000 rows — 5 part types with JSON BOM
│   ├── warranty_claims.csv      # 600 rows — free-text complaints and tech notes
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
