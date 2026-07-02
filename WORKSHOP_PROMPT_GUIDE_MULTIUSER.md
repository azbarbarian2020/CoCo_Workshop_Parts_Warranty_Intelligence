# CoCo Workshop: Parts Warranty Intelligence (Multi-User Version)

## Prompt Guide & Talk Track

**Duration**: ~30 minutes
**Platform**: Cortex Code (CoCo) in Snowsight
**Database**: `<YOUR_USER>_COCO_WORKSHOP` (created by 00_setup_multiuser.sql)
**Schemas**: BRONZE, SILVER, GOLD
**Warehouse**: `<YOUR_USER>_COCO_WORKSHOP_WH` (Gen2 Medium)

**Pre-requisite**: Run `sql/00_setup_multiuser.sql` first. It creates your user-prefixed database and warehouse.

---

## Architecture Overview

```
BRONZE (Raw)                    SILVER (Enriched)              GOLD (Analytics-Ready)
+-----------------+             +------------------------+     +------------------+
| SUPPLIER_RAW    |──────────────────────────────────────────▶| SUPPLIERS        |
| (12 rows, dirty)|             |                        |     | (10 rows, clean) |
+-----------------+             |                        |     +------------------+
                                |                        |
+-----------------+             |                        |     +------------------+
| PARTS_RAW       |──────────────────────────────────────────▶| PARTS            |
| (25000 rows,BOM|             |                        |     | (175000 rows,    |
|  JSON arrays)   |             |                        |     |  flattened BOM)  |
+-----------------+             |                        |     +------------------+
                                |                        |            |
+-----------------+   AI_SUMMARIZE  +--------------------+            |
| WARRANTY_CLAIMS |──────────────▶| COMPLAINT_SUMMARIES  |            |
| _RAW            |   AI_COMPLETE  +--------------------+            |
| (600 rows)      |──────────────▶| SYMPTOM_CATEGORIES   |            |
|                 |   AI_CLASSIFY  +--------------------+            |
|                 |──────────────▶| WARRANTY_CLAIMS      |   AI_CLASSIFY   +------------------+
|                 |               | (+symptom_category)  |──────────────▶| WARRANTY_CLAIMS  |
+-----------------+               +------------------------+     | (+failed_sub_part)|
                                                                 +------------------+
                                                                          |
                                                            Semantic View ▼
                                                     +----------------------------+
                                                     | WARRANTY_ANALYTICS         |
                                                     +----------------------------+
                                                                          |
+-----------------+                                          Cortex Search ▼
| @BRONZE.DOCS    |     PARSE_DOCUMENT    +------------------+    +----------------------------+
| (5 PDF manuals) |────────────────────▶| DOCS_EMBEDDINGS  |───▶| PARTS_MANUAL_SEARCH      |
+-----------------+     + chunking       | (chunked text)   |    | (Cortex Search Service)  |
                                         +------------------+    +----------------------------+
                                                                          |
                                                              Cortex Agent ▼
                                                     +----------------------------+
                                                     | WARRANTY_AGENT             |
                                                     +----------------------------+
```

---

## Step 0: Set Context

```
My workshop database is prefixed with my Snowflake username: <username>_COCO_WORKSHOP, and my warehouse is <username>_COCO_WORKSHOP_WH. Use those for this entire session. When I reference COCO_WORKSHOP in my prompts, always use my user-prefixed version.
```

> **Talk track**: "CoCo knows who I am. I'm telling it my personal database and warehouse names — everything I build goes there."

---

## ACT 1: Data Engineering (Bronze to Gold)

### Step 1: Clean Supplier Data

**PROMPT**:

```
Analyze BRONZE.SUPPLIER_RAW for data quality issues.
```

> **Talk track**: "I'm just asking CoCo to look at it — I'm not telling it what's wrong. Watch it discover the problems on its own."

CoCo will identify the issues. Then follow up:

```
Clean BRONZE.SUPPLIER_RAW into a new table GOLD.SUPPLIERS. Fix the issues you identified.
```

> **Talk track**: "One follow-up prompt and CoCo writes the entire cleaning pipeline — deduplication, case normalization, state standardization, trimming."

**RESULT**: GOLD.SUPPLIERS — 10 clean rows.

---

### Step 2: Flatten Parts BOM

**PROMPT**:

```
Flatten the BOM JSON array in BRONZE.PARTS_RAW into a new table GOLD.PARTS with one row per serial_number, sub_part combination. Include part_number, serial_number, sub_part, supplier_id, and batch_id.
```

> **Talk track**: "The parts data is nested JSON — each serial number has 7 sub-parts stuffed into one column. CoCo uses LATERAL FLATTEN to explode this into a proper relational table. 25,000 rows become 175,000."

**RESULT**: GOLD.PARTS — 175,000 rows.

---

## ACT 2: AI/ML Enrichment (Bronze to Silver to Gold)

### Step 3: Summarize Complaints by Part

**PROMPT**:

```
Summarize all customer_complaint values in BRONZE.WARRANTY_CLAIMS_RAW grouped by part_number. Save to SILVER.COMPLAINT_SUMMARIES.
```

> **Talk track**: "We have 600 free-text complaints. Instead of reading them all, I ask Snowflake's built-in AI to summarize them by part type. One function call — no external API, no tokens to manage."

**RESULT**: SILVER.COMPLAINT_SUMMARIES — 5 rows (one per part type).

---

### Step 4: Discover Symptom Categories

**PROMPT 4a** (ask CoCo directly):

```
What are the 20 most common categories for describing major mechanical issues with big rig trucks using plain driver language? List only the category names, no descriptions.
```

> **Talk track**: "I'm just asking CoCo for domain knowledge — no SQL needed."

CoCo returns a list. Then:

**PROMPT 4b**:

```
Using llama3.1-70b, compare those 20 categories against the summaries in SILVER.COMPLAINT_SUMMARIES and select the 10 that best match our data. Save each as a row in SILVER.SYMPTOM_CATEGORIES.
```

> **Talk track**: "Now I'm combining LLM domain knowledge with our actual data. It picks the 10 categories that best describe what we're seeing."

**RESULT**: SILVER.SYMPTOM_CATEGORIES — 10 rows.

---

### Step 5: Classify Complaints by Symptom

**PROMPT**:

```
Classify each customer_complaint in BRONZE.WARRANTY_CLAIMS_RAW into one of the categories from SILVER.SYMPTOM_CATEGORIES. Save as SILVER.WARRANTY_CLAIMS with all original columns plus a symptom_category column.
```

> **Talk track**: "AI_CLASSIFY reads each complaint and assigns the best-matching symptom category. No training data, no fine-tuning — it just works."

**TIMING**: ~1-3 minutes (600 AI_CLASSIFY calls).

**RESULT**: SILVER.WARRANTY_CLAIMS — 600 rows + SYMPTOM_CATEGORY.

---

### Step 6: Classify Failed Sub-Parts

**PROMPT**:

```
For each claim in SILVER.WARRANTY_CLAIMS, classify which sub-part failed based on technician_notes. Use the distinct sub_parts from GOLD.PARTS for that claim's part_number as categories. Focus on root cause — the component that failed, not downstream effects. Save as GOLD.WARRANTY_CLAIMS with a failed_sub_part column.
```

> **Talk track**: "This is the magic moment. The AI reads each technician's repair notes and figures out which sub-component actually failed. Now we can trace failures back to specific suppliers and batches."

**TIMING**: ~2-5 minutes (longest step).

**RESULT**: GOLD.WARRANTY_CLAIMS — 600 rows + FAILED_SUB_PART.

---

## ACT 3: Semantic View & Agent Assembly

### Step 7: Create the Semantic View

**PROMPT**:

```
/semantic_studio Create a semantic view called GOLD.WARRANTY_ANALYTICS over GOLD.WARRANTY_CLAIMS, GOLD.PARTS, and GOLD.SUPPLIERS. WARRANTY_CLAIMS joins to PARTS on SERIAL_NUMBER and FAILED_SUB_PART = SUB_PART. PARTS joins to SUPPLIERS on SUPPLIER_ID. Include PART_NUMBER as a dimension on both WARRANTY_CLAIMS and PARTS. Include a UNIT_COUNT metric as COUNT(DISTINCT PARTS.SERIAL_NUMBER). Add synonyms: 'vendor' = COMPANY_NAME, 'component' = SUB_PART.
```

> **Talk track**: "The semantic view is the bridge between natural language and SQL. I'm defining table relationships, metrics, and hints — pure SQL DDL, no YAML files."

**RESULT**: Semantic view GOLD.WARRANTY_ANALYTICS.

---

### Step 8: Create Cortex Search Service

**PROMPT**:

```
Create a Cortex Search Service called GOLD.PARTS_MANUAL_SEARCH over the PDFs in @BRONZE.DOCS. Parse and chunk them first into BRONZE.DOCS_EMBEDDINGS.
```

> **Talk track**: "One prompt — CoCo parses the PDFs, chunks the text, and creates a searchable index. Now the AI can look up torque specs and procedures directly from the source documents."

**If CoCo stalls**, split into two prompts:

> ```
> Parse the 5 PDF files from @BRONZE.DOCS and chunk the text into ~500 token rows. Save to BRONZE.DOCS_EMBEDDINGS with columns: file_name, chunk_index, chunk_text.
> ```
> Then:
> ```
> Create a Cortex Search Service called GOLD.PARTS_MANUAL_SEARCH on the chunk_text column of BRONZE.DOCS_EMBEDDINGS.
> ```

**RESULT**: GOLD.PARTS_MANUAL_SEARCH (active Cortex Search Service).

---

### Step 9: Create the Cortex Agent (Grand Finale)

**PROMPT**:

```
Create a Cortex Agent called GOLD.WARRANTY_AGENT that combines the GOLD.PARTS_MANUAL_SEARCH search service and the GOLD.WARRANTY_ANALYTICS semantic view. In the agent instructions, specify that all questions about failure rates, claims, parts, or suppliers must use the WARRANTY_ANALYTICS semantic view tool.
```

> **Talk track**: "One prompt. We just built an AI agent that combines structured data analytics with document search. No API integration, no RAG framework — just declare the tools and Snowflake handles the orchestration."

**RESULT**: GOLD.WARRANTY_AGENT — Cortex Agent with two tools.

---

## Testing the Agent

After the agent is created, test with these 4 questions.

### Q1: The Heat Map

```
Show me the parent part failure rates by symptom description in a heat map
```

### Q2: Top Failures Drill-Down

```
Show me the top 5 failure rates for all parts, sub-parts, and vendors, grouped in that order in descending order
```

> **Expected**: Piston and Cylinder Kit (3 vendors at ~2-4%), VGT Actuator (~2.9%), Main PCB (~2.9%). If results show 100%, add a VQR — see Troubleshooting.

### Q3: Root Cause Analysis

```
Evaluate failures for Main PCB and VGT Actuator sub parts down to the vendor and batch level to determine if the issues appear to be more of a vendor problem or a batch problem.
```

### Q4: Cross-Tool — Data + Docs

```
What are possible cascading effects of a Main PCB going out in a TCM-3200?
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Q2 returns 100% failure rates | Add a VQR: `/semantic_studio Add a verified query to GOLD.WARRANTY_ANALYTICS for "Show me the top 5 failure rates..." with SQL that computes UNIT_COUNT from PARTS in a separate CTE before joining to claims.` |
| Agent "Analyst tool missing execution environment" | Edit agent in Snowsight → add your warehouse to the semantic view tool's execution settings |
| AI_CLASSIFY returns empty strings | Add `task_description` to the config object |
| Semantic view creation fails | Ensure PRIMARY KEY is defined on referenced table's join columns |
| CoCo uses wrong database | Re-run Step 0 to remind it of your user-prefixed database |

---

## Cleanup

```sql
-- Replace <USER> with your username
DROP AGENT IF EXISTS <USER>_COCO_WORKSHOP.GOLD.WARRANTY_AGENT;
DROP CORTEX SEARCH SERVICE IF EXISTS <USER>_COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH;
DROP SEMANTIC VIEW IF EXISTS <USER>_COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.GOLD.WARRANTY_CLAIMS;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.GOLD.PARTS;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.GOLD.SUPPLIERS;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.SILVER.WARRANTY_CLAIMS;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.SILVER.SYMPTOM_CATEGORIES;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.SILVER.COMPLAINT_SUMMARIES;
DROP TABLE IF EXISTS <USER>_COCO_WORKSHOP.BRONZE.DOCS_EMBEDDINGS;
DROP DATABASE IF EXISTS <USER>_COCO_WORKSHOP;
DROP WAREHOUSE IF EXISTS <USER>_COCO_WORKSHOP_WH;
```
