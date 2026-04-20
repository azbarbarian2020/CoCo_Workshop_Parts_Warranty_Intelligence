# CoCo Workshop: Parts Warranty Intelligence

## Prompt Guide & Talk Track

**Duration**: ~30 minutes
**Platform**: Cortex Code (CoCo)
**Database**: COCO_WORKSHOP
**Schemas**: BRONZE, SILVER, GOLD
**Warehouse**: COCO_WORKSHOP_WH (Gen2 Medium)

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
| (500 rows)      |──────────────▶| SYMPTOM_CATEGORIES   |            |
|                 |   AI_CLASSIFY  +--------------------+            |
|                 |──────────────▶| WARRANTY_CLAIMS      |   AI_CLASSIFY   +------------------+
|                 |               | (+symptom_category)  |──────────────▶| WARRANTY_CLAIMS  |
+-----------------+               +------------------------+     | (+failed_sub_part)|
                                                                 +------------------+
                                                                          |
                                                            Semantic View ▼
                                                     +----------------------------+
                                                     | WARRANTY_ANALYTICS         |
                                                     | (3 tables, 2 joins,        |
                                                     |  metrics + dimensions)     |
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
                                                     | (semantic view + search)   |
                                                     +----------------------------+
```

**Medallion layers:**
- **Bronze**: Raw ingested data. Messy, unstructured, as-is from source systems.
- **Silver**: AI-enriched intermediary. Cortex AI functions summarize, categorize, and classify.
- **Gold**: Analytics-ready. Clean, flat, joined. The semantic view sits on top.

---

## Bronze Tables (Pre-loaded)

| Table | Rows | Description |
|-------|------|-------------|
| SUPPLIER_RAW | 12 | Supplier master data with data quality issues (inconsistent casing, state formats, extra spaces, duplicates) |
| PARTS_RAW | 25,000 | 5 part types x 5,000 serial numbers. BOM column is a JSON array of sub-parts with supplier_id and batch_id |
| WARRANTY_CLAIMS_RAW | 500 | Raw warranty claims with free-text customer_complaint and technician_notes |
| @BRONZE.DOCS | 5 PDFs | Parts service manuals (one per part type), directory enabled |

---

## Data Stories Embedded in the Data

Three distinct failure patterns are embedded for discovery during the demo:

| Story | Sub-Part | Pattern | What You Find |
|-------|----------|---------|---------------|
| **Bad Batch** | VGT Actuator | Three suppliers (Precision Dynamics 40%, Allied Turbo 35%, ThermalTech 25%). Precision Dynamics batch B-2024-PD-VA-07 has 5.7% failure rate vs <1.3% for all other batches. | Isolate the batch, issue a recall. |
| **Bad Supplier** | Main PCB | Three suppliers (NovaTech 40%, Berg Elektronik 35%, Precision Dynamics 25%). NovaTech: 3.07% failure rate. Others: 0-0.23%. | Switch suppliers or escalate quality audit. |
| **Design Problem** | Piston and Cylinder Kit | Three suppliers (Midwest Pneumatics 40%, Great Lakes 35%, Heartland Steel 25%). All fail at similar rates (0.93-1.16%). | Not a supplier or batch issue — redesign needed. |

---

## Step 0: Set Context

**WHY**: Tell CoCo which database and warehouse to use for the entire session.

**PROMPT**:

```
Use database COCO_WORKSHOP and warehouse COCO_WORKSHOP_WH for this session.
```

> **Talk track**: "First we point CoCo at our workshop database and Gen2 warehouse. Everything we build will live here."

---

## ACT 1: Data Engineering (Bronze to Gold)

### Step 1: Clean Supplier Data

**WHY**: SUPPLIER_RAW has 12 rows but only 10 real suppliers. It contains inconsistent company name casing ("NOVATECH ELECTRONICS, LLC" vs "Precision Dynamics LLC"), full state names mixed with abbreviations ("Illinois" vs "CA"), leading/trailing spaces, inconsistent country values ("US" vs "USA" vs "United States"), and duplicate rows. CoCo should find and fix all of this.

**PROMPT** (copy/paste into CoCo):

```
Analyze COCO_WORKSHOP.BRONZE.SUPPLIER_RAW for data quality issues.

```

> **Talk track**: "Let's start with the dirtiest table. I'm just asking CoCo to look at it — I'm not telling it what's wrong. Watch it discover the problems on its own."

CoCo will identify the issues. Then follow up:

```
Clean COCO_WORKSHOP.BRONZE.SUPPLIER_RAW into a new table COCO_WORKSHOP.GOLD.SUPPLIERS. Fix the issues you identified.
```

> **Talk track**: "One follow-up prompt and CoCo writes the entire cleaning pipeline — deduplication, case normalization, state standardization, trimming. No pandas, no dbt, just natural language."

**RESULT**: GOLD.SUPPLIERS — 10 clean rows, proper casing, 2-letter state codes, consistent "US" country.

---

### Step 2: Flatten Parts BOM

**WHY**: PARTS_RAW stores the bill of materials as a JSON array in a single BOM column. Each serial number has one row with a JSON array containing 7 sub-parts, each with a supplier_id and batch_id. Three key sub-parts (VGT Actuator, Main PCB, Piston & Cylinder Kit) are multi-sourced from 2-3 suppliers. We need to flatten this into a relational format — one row per serial_number + sub_part — so we can join to warranty claims and suppliers.

**PROMPT**:

```
Flatten the BOM JSON array in COCO_WORKSHOP.BRONZE.PARTS_RAW into a new table COCO_WORKSHOP.GOLD.PARTS with one row per serial_number, sub_part combination. Include part_number, serial_number, sub_part, supplier_id, and batch_id.
```

> **Talk track**: "The parts data is nested JSON — each serial number has 7 sub-parts stuffed into one column. CoCo uses LATERAL FLATTEN to explode this into a proper relational table. 25,000 rows become 175,000."

**RESULT**: GOLD.PARTS — 175,000 rows (25,000 serial numbers x 7 sub-parts each). Columns: PART_NUMBER, SERIAL_NUMBER, SUB_PART, SUPPLIER_ID, BATCH_ID.

---

## ACT 2: AI/ML Enrichment (Bronze to Silver to Gold)

### Step 3: Summarize Complaints by Part

**WHY**: We have 500 warranty claims with free-text customer complaints. Before we can classify them, we need to understand what kinds of complaints exist for each part type. AI_SUMMARIZE_AGG condenses hundreds of complaints per part into a single summary paragraph — giving us a high-level view of failure patterns.

**PROMPT**:

```
Summarize all customer_complaint values in COCO_WORKSHOP.BRONZE.WARRANTY_CLAIMS_RAW grouped by part_number using AI_SUMMARIZE_AGG. Save to COCO_WORKSHOP.SILVER.COMPLAINT_SUMMARIES.
```

> **Talk track**: "We have 500 free-text complaints. Instead of reading them all, I'll ask Snowflake's built-in AI to summarize them by part type. One SQL function call — no external API, no tokens to manage."

**RESULT**: SILVER.COMPLAINT_SUMMARIES — 5 rows (one per part type), each with a paragraph summarizing the common complaint themes.

---

### Step 4: Discover Symptom Categories

**WHY**: We need a controlled vocabulary of symptom categories to classify complaints. Instead of manually curating a list, we use a two-step AI approach: first ask the LLM for general trucking symptom categories, then refine against our actual data.

**PROMPT 4a** (ask CoCo directly, no SQL needed):

```
What are the 20 most common and unique categories for describing major mechanical issues with big rig trucks using plain driver language?
```

> **Talk track**: "I'm not writing SQL here — I'm just asking CoCo for domain knowledge. It knows trucking terminology because the underlying LLM was trained on it."

CoCo returns a list of ~20 categories. Copy the list, then:

**PROMPT 4b**:

```
Using COMPLETE with llama3.1-70b, compare these categories against the summaries in COCO_WORKSHOP.SILVER.COMPLAINT_SUMMARIES and select the 10 that best match our data. Save each as a row in COCO_WORKSHOP.SILVER.SYMPTOM_CATEGORIES: [paste the list from 4a here]
```

> **Talk track**: "Now I'm combining the LLM's domain knowledge with our actual complaint summaries. It reads both and picks the 10 categories that best describe what we're actually seeing. This is the kind of human-in-the-loop AI workflow that CoCo makes easy."

**RESULT**: SILVER.SYMPTOM_CATEGORIES — 10 rows, each a distinct symptom category tailored to our data (e.g., "Engine Overheating", "Electrical Failure", "Exhaust System Issues", etc.)

---

### Step 5: Classify Complaints by Symptom

**WHY**: Now we tag each of the 500 warranty claims with one of our 10 symptom categories. This turns unstructured text into a filterable, groupable dimension. AI_CLASSIFY is Snowflake's built-in classification function — it reads the text and picks the best matching label from a provided list.

**PROMPT**:

```
Using AI_CLASSIFY with task_description 'Classify the truck driver warranty complaint into the primary symptom category', classify each customer_complaint in COCO_WORKSHOP.BRONZE.WARRANTY_CLAIMS_RAW using the categories from COCO_WORKSHOP.SILVER.SYMPTOM_CATEGORIES. Save as COCO_WORKSHOP.SILVER.WARRANTY_CLAIMS with all original columns plus a symptom_category column.
```

> **Talk track**: "AI_CLASSIFY reads each complaint and assigns the best-matching symptom category. No training data, no fine-tuning — it just works."

**TIMING**: ~1-3 minutes. AI_CLASSIFY makes one LLM inference call per row (500 calls). Execution time varies by region and Cortex AI load.

**RESULT**: SILVER.WARRANTY_CLAIMS — 500 rows, all original columns + SYMPTOM_CATEGORY.

---

### Step 6: Classify Failed Sub-Parts

**WHY**: This is the key enrichment step. Each warranty claim describes a failure in the technician's notes, but doesn't say WHICH sub-part failed. We use AI_CLASSIFY to read the technician_notes and determine which of the 7 possible sub-parts (from the GOLD.PARTS table) is the failed component. This enables root cause analysis by sub-part, supplier, and batch.

**PROMPT**:

```
Using AI_CLASSIFY with task_description 'Identify which single sub-component caused the warranty claim failure based on technician repair notes', classify each claim in COCO_WORKSHOP.SILVER.WARRANTY_CLAIMS by the failed sub-part. For each claim, use the distinct sub_part values from COCO_WORKSHOP.GOLD.PARTS matching that claim's part_number as the categories. Classify the technician_notes column. Save as COCO_WORKSHOP.GOLD.WARRANTY_CLAIMS with all columns plus a failed_sub_part column.
```

> **Talk track**: "This is the magic moment. The AI reads each technician's repair notes and figures out which sub-component actually failed. It uses the parts BOM as the category list — so for a turbocharger claim, it chooses from VGT Actuator, Compressor Wheel, Bearing Housing, etc. Now we can trace failures back to specific suppliers and batches."

**TIMING**: ~2-5 minutes. This is the longest-running step — each of the 500 claims requires an AI_CLASSIFY call with a correlated subquery to look up the sub-parts for that claim's part type. Let it run.

**RESULT**: GOLD.WARRANTY_CLAIMS — 500 rows, all columns + FAILED_SUB_PART. This is the final claims table.

---

## ACT 3: Semantic View & Agent Assembly

### Step 7: Create the Semantic View

**WHY**: A semantic view tells Cortex Analyst how to translate natural language questions into SQL. It defines which tables exist, how they join, what the metrics are, and what each column means. Without it, the AI agent wouldn't know that "vendor" means COMPANY_NAME or that failure rate = claims / total deployed parts.

**PROMPT**:

```
$semantic-view Create a semantic view called COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS over COCO_WORKSHOP.GOLD.WARRANTY_CLAIMS, COCO_WORKSHOP.GOLD.PARTS, and COCO_WORKSHOP.GOLD.SUPPLIERS. WARRANTY_CLAIMS joins to PARTS on SERIAL_NUMBER and FAILED_SUB_PART = SUB_PART. PARTS joins to SUPPLIERS on SUPPLIER_ID. Include a UNIT_COUNT metric as COUNT(DISTINCT PARTS.SERIAL_NUMBER) for failure rate denominators — failure rate should be calculated as claim count divided by UNIT_COUNT. Add synonyms so 'vendor' maps to COMPANY_NAME and 'component' maps to SUB_PART. Use pure SQL DDL.
```

> **Talk track**: "The semantic view is the bridge between natural language and SQL. I'm defining the table relationships, the metrics, and giving the AI hints about how to calculate failure rates. Notice I'm using pure SQL — no YAML files, no staging, just DDL."

**RESULT**: Semantic view COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS with 3 tables, 2 relationships, metrics + dimensions.

### Step 8: Create Cortex Search Service

**WHY**: The Gold tables give us structured analytics, but technicians also need to look up specs, torque values, and troubleshooting procedures from the parts manuals. A Cortex Search Service indexes the 5 PDF manuals so the AI agent can answer document questions alongside data questions.

**PROMPT**:

```
Create a Cortex Search Service called COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH over the PDF files in the @COCO_WORKSHOP.BRONZE.DOCS stage. Use warehouse COCO_WORKSHOP_WH. First parse and chunk the PDFs into a table called COCO_WORKSHOP.BRONZE.DOCS_EMBEDDINGS, then create the search service in the GOLD schema on top of it.
```

> **Talk track**: "We have 5 PDF parts manuals sitting on a Snowflake stage. With one prompt, CoCo parses the PDFs, chunks the text, and creates a searchable index. Now the AI can answer questions like 'what's the torque spec for a turbocharger mounting bolt?' directly from the source documents."

**RESULT**: BRONZE.DOCS_EMBEDDINGS (chunked text from 5 PDFs) and GOLD.PARTS_MANUAL_SEARCH (Cortex Search Service, active).

---

### Step 9: Create the Cortex Agent (Grand Finale)

**WHY**: This is the payoff. A Cortex Agent combines the semantic view (structured warranty data) with the search service (parts manual documents) into a single conversational interface. One agent that can answer both "what's our failure rate for VGT Actuators?" and "what does the manual say about actuator inspection?" — and combine both in a single answer.

**PROMPT**:

```
Create a Cortex Agent called COCO_WORKSHOP.GOLD.WARRANTY_AGENT that combines:
1. The COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH Cortex Search Service for looking up parts manual specs and procedures
2. The COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS semantic view for querying warranty claims, parts, and supplier data
Use warehouse COCO_WORKSHOP_WH.
```

> **Talk track**: "One prompt. We just built an AI agent that combines structured data analytics with unstructured document search. No API integration, no RAG framework, no vector database plumbing — just declare what tools the agent has and Snowflake handles the orchestration."

**RESULT**: GOLD.WARRANTY_AGENT — a Cortex Agent with two tools: query_warranty_data (semantic view) and search_parts_manuals (Cortex Search).

---

## Testing the Agent

After the agent is created, test it with these 4 questions. The flow tells a story: big picture → drill-down → root cause analysis → document search.

### Q1: The Heat Map

```
Show me the parent part failure rates by symptom description in a heat map
```

> **What it shows**: The AI_CLASSIFY enrichment from Act 2 (SYMPTOM_CATEGORY) combined with multi-table join. Proves the unstructured customer complaints were turned into a queryable dimension. The agent returns a part × symptom matrix — you can visualize this as a heat map to see where problems cluster.

### Q2: Top Failures Drill-Down

```
Show me the top 5 failure rates for all parts, sub-parts, and vendors, grouped in that order in descending order
```

> **What it shows**: Three-table join, UNIT_COUNT-based failure rate calculation. All three stories surface immediately — VGT Actuator from Precision Dynamics at the top, Main PCB from NovaTech, and Piston and Cylinder Kit spread across all vendors at similar rates.

### Q3: Root Cause Analysis (Bad Supplier vs Bad Batch)

```
Analyze the failure rates for the Main PCB and VGT Actuator to determine if the majority of failures appear to be a vendor issue or batch issue and why
```

> **What it shows**: The money question. The agent must reason about two different failure patterns:
> - **Main PCB**: NovaTech (SUP-002) has 3.07% failure rate while Berg Elektronik has 0% and Precision Dynamics 0.23%. Failures span ALL NovaTech batches → bad supplier.
> - **VGT Actuator**: Precision Dynamics (SUP-001) has elevated failures, but drill into batches and batch B-2024-PD-VA-07 is the outlier at 5.7% while other batches are <1.3% → bad batch.
> This question forces the agent to compare suppliers AND batches, surfacing both patterns in one answer.

### Q4: Cross-Tool — Data + Docs (The Wow Moment)

```
What are possible cascading effects of a Main PCB going out in a TCM-3200?
```

> **What it shows**: First time the audience sees the search tool fire. The agent pulls from the TCM-3200 parts manual to explain how a Main PCB failure can cascade to other sub-components (solenoid pack burnout from incorrect line pressure commands, pressure transducer damage from overcurrent sensing, wiring harness issues). This demonstrates the agent reasoning across structured warranty data AND unstructured PDF documents in a single answer.

---

## Quick Reference: What Each AI Function Does

| Function | What It Does | Where We Use It |
|----------|-------------|-----------------|
| **AI_SUMMARIZE_AGG** | Aggregates and summarizes multiple text values into one paragraph | Step 3: Summarize 500 complaints into 5 part-level summaries |
| **COMPLETE** (llama3.1-70b) | General-purpose LLM for text generation and reasoning | Step 4b: Select 10 best symptom categories from 20 candidates |
| **AI_CLASSIFY** | Classifies text into one of N provided categories | Step 5: Tag complaints with symptom categories. Step 6: Identify failed sub-parts from technician notes. |
| **PARSE_DOCUMENT** | Extracts text content from PDF/image files on a stage | Step 8: Parse parts manual PDFs into searchable text chunks |

---

## Quick Reference: Table & Service Lineage

| Asset | Source | Transformation |
|-------|--------|----------------|
| GOLD.WARRANTY_AGENT | WARRANTY_ANALYTICS + PARTS_MANUAL_SEARCH | Cortex Agent combining structured data + document search |
| GOLD.PARTS_MANUAL_SEARCH | BRONZE.DOCS_EMBEDDINGS | Cortex Search Service over chunked PDF text |
| GOLD.WARRANTY_ANALYTICS | GOLD.WARRANTY_CLAIMS + GOLD.PARTS + GOLD.SUPPLIERS | Semantic view: 3 tables, 2 joins, metrics + dimensions |
| GOLD.SUPPLIERS | BRONZE.SUPPLIER_RAW | Dedup, normalize casing, standardize states/country, trim spaces |
| GOLD.PARTS | BRONZE.PARTS_RAW | LATERAL FLATTEN on BOM JSON array, extract sub_part/supplier_id/batch_id |
| GOLD.WARRANTY_CLAIMS | SILVER.WARRANTY_CLAIMS + GOLD.PARTS | AI_CLASSIFY technician_notes against sub-part categories per part_number |
| BRONZE.DOCS_EMBEDDINGS | @BRONZE.DOCS (5 PDFs) | PARSE_DOCUMENT + text chunking |
| SILVER.WARRANTY_CLAIMS | BRONZE.WARRANTY_CLAIMS_RAW + SILVER.SYMPTOM_CATEGORIES | AI_CLASSIFY customer_complaint against 10 symptom categories |
| SILVER.COMPLAINT_SUMMARIES | BRONZE.WARRANTY_CLAIMS_RAW | AI_SUMMARIZE_AGG grouped by part_number |
| SILVER.SYMPTOM_CATEGORIES | SILVER.COMPLAINT_SUMMARIES + LLM knowledge | COMPLETE selects 10 best categories from 20 LLM-generated candidates |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| AI_CLASSIFY returns empty strings | Add `task_description` to the config object — it dramatically improves accuracy |
| AI_CLASSIFY JSON path wrong | AI_CLASSIFY returns `{"labels":["value"]}` — extract with `['labels'][0]::VARCHAR`, NOT `:label::VARCHAR` |
| AI_SUMMARIZE_AGG unknown function | Use `AI_SUMMARIZE_AGG(...)` without the `SNOWFLAKE.CORTEX.` schema prefix |
| Semantic view creation fails with "referenced key must be primary or unique" | Ensure PRIMARY KEY is defined on the referenced table's join columns |
| SEMANTIC_VIEW query fails with "multiple columns" | You can't mix metrics from different tables in one SEMANTIC_VIEW() call — use Cortex Analyst instead |
| COMPLETE returns malformed output | Specify the model explicitly: `SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', prompt)` |
| Semantic view has 0 metrics | Use `metrics` with full aggregate expressions (e.g., `COUNT(TABLE.COL)`), not `measures` or `default_aggregation` |
| Agent spec "unrecognized field" | Use `tool_spec.type/name/description` format, NOT `tool_type/tool_name`. `tool_resources` is top-level keyed by tool name. |

---

## Cleanup

```sql
-- Drop demo artifacts (preserves Bronze for re-run)
DROP AGENT IF EXISTS COCO_WORKSHOP.GOLD.WARRANTY_AGENT;
DROP CORTEX SEARCH SERVICE IF EXISTS COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH;
DROP SEMANTIC VIEW IF EXISTS COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS;
DROP TABLE IF EXISTS COCO_WORKSHOP.GOLD.WARRANTY_CLAIMS;
DROP TABLE IF EXISTS COCO_WORKSHOP.GOLD.PARTS;
DROP TABLE IF EXISTS COCO_WORKSHOP.GOLD.SUPPLIERS;
DROP TABLE IF EXISTS COCO_WORKSHOP.SILVER.WARRANTY_CLAIMS;
DROP TABLE IF EXISTS COCO_WORKSHOP.SILVER.SYMPTOM_CATEGORIES;
DROP TABLE IF EXISTS COCO_WORKSHOP.SILVER.COMPLAINT_SUMMARIES;
DROP TABLE IF EXISTS COCO_WORKSHOP.BRONZE.DOCS_EMBEDDINGS;
-- Bronze tables and stages are preserved for re-running the demo
```
