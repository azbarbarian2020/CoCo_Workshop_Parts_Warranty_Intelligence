# CoCo Workshop: Parts Warranty Intelligence

## Prompt Guide & Talk Track

**Duration**: ~30 minutes
**Platform**: Cortex Code (CoCo) in Snowsight
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
| WARRANTY_CLAIMS_RAW | 600 | Raw warranty claims with free-text customer_complaint and technician_notes |
| @BRONZE.DOCS | 5 PDFs | Parts service manuals (one per part type), directory enabled |

---

## Data Stories Embedded in the Data

Three distinct failure patterns are embedded for discovery during the demo:

| Story | Sub-Part | Pattern | What You Find |
|-------|----------|---------|---------------|
| **Bad Batch** | VGT Actuator | Three suppliers (Precision Dynamics 40%, Allied Turbo 35%, ThermalTech 25%). Precision Dynamics batch B-2024-PD-VA-07 has elevated failure rate vs other batches. | Isolate the batch, issue a recall. |
| **Bad Supplier** | Main PCB | Three suppliers (NovaTech 40%, Berg Elektronik 35%, Precision Dynamics 25%). NovaTech has significantly elevated failure rate. Others near zero. | Switch suppliers or escalate quality audit. |
| **Design Problem** | Piston and Cylinder Kit | Three suppliers (Midwest Pneumatics 40%, Great Lakes 35%, Heartland Steel 25%). All fail at similar elevated rates (2-4%). | Not a supplier or batch issue — redesign needed. |

---

## Step 0: Set Context

```
Use database COCO_WORKSHOP and warehouse COCO_WORKSHOP_WH for this session.
```

> **Talk track**: "First we point CoCo at our workshop database and Gen2 warehouse. Everything we build will live here."

---

## ACT 1: Data Engineering (Bronze to Gold)

### Step 1: Clean Supplier Data

**WHY**: SUPPLIER_RAW has 12 rows but only 10 real suppliers — duplicates, inconsistent casing, mixed state formats, extra spaces.

**PROMPT**:

```
Analyze COCO_WORKSHOP.BRONZE.SUPPLIER_RAW for data quality issues.
```

> **Talk track**: "I'm just asking CoCo to look at it — I'm not telling it what's wrong. Watch it discover the problems on its own."

CoCo will identify the issues. Then follow up:

```
Clean COCO_WORKSHOP.BRONZE.SUPPLIER_RAW into a new table COCO_WORKSHOP.GOLD.SUPPLIERS. Fix the issues you identified.
```

> **Talk track**: "One follow-up prompt and CoCo writes the entire cleaning pipeline — deduplication, case normalization, state standardization, trimming."

**RESULT**: GOLD.SUPPLIERS — 10 clean rows.

---

### Step 2: Flatten Parts BOM

**WHY**: PARTS_RAW stores the bill of materials as a JSON array. We need one row per serial_number + sub_part.

**PROMPT**:

```
Flatten the BOM JSON array in COCO_WORKSHOP.BRONZE.PARTS_RAW into a new table COCO_WORKSHOP.GOLD.PARTS with one row per serial_number, sub_part combination. Include part_number, serial_number, sub_part, supplier_id, and batch_id.
```

> **Talk track**: "The parts data is nested JSON — each serial number has 7 sub-parts stuffed into one column. CoCo uses LATERAL FLATTEN to explode this into a proper relational table. 25,000 rows become 175,000."

**RESULT**: GOLD.PARTS — 175,000 rows.

---

## ACT 2: AI/ML Enrichment (Bronze to Silver to Gold)

### Step 3: Summarize Complaints by Part

**WHY**: We need a high-level view of complaint patterns before classifying. AI_SUMMARIZE_AGG condenses hundreds of complaints per part into one paragraph.

**PROMPT**:

```
Summarize all customer_complaint values in COCO_WORKSHOP.BRONZE.WARRANTY_CLAIMS_RAW grouped by part_number. Save to COCO_WORKSHOP.SILVER.COMPLAINT_SUMMARIES.
```

> **Talk track**: "We have 600 free-text complaints. Instead of reading them all, I ask Snowflake's built-in AI to summarize them by part type. One function call — no external API, no tokens to manage."

**RESULT**: SILVER.COMPLAINT_SUMMARIES — 5 rows (one per part type).

---

### Step 4: Discover Symptom Categories

**WHY**: We need a controlled vocabulary of symptom categories. We use a two-step AI approach: ask for general trucking categories, then refine against our data.

**PROMPT 4a** (ask CoCo directly):

```
What are the 20 most common categories for describing major mechanical issues with big rig trucks using plain driver language? List only the category names, no descriptions.
```

> **Talk track**: "I'm just asking CoCo for domain knowledge — no SQL needed."

CoCo returns a list. Then:

**PROMPT 4b**:

```
Using llama3.1-70b, compare those 20 categories against the summaries in COCO_WORKSHOP.SILVER.COMPLAINT_SUMMARIES and select the 10 that best match our data. Save each as a row in COCO_WORKSHOP.SILVER.SYMPTOM_CATEGORIES.
```

> **Talk track**: "Now I'm combining LLM domain knowledge with our actual data. It picks the 10 categories that best describe what we're seeing."

**RESULT**: SILVER.SYMPTOM_CATEGORIES — 10 rows.

---

### Step 5: Classify Complaints by Symptom

**WHY**: Tag each warranty claim with a symptom category, turning free text into a filterable dimension.

**PROMPT**:

```
Classify each customer_complaint in COCO_WORKSHOP.BRONZE.WARRANTY_CLAIMS_RAW into one of the categories from COCO_WORKSHOP.SILVER.SYMPTOM_CATEGORIES. Save as COCO_WORKSHOP.SILVER.WARRANTY_CLAIMS with all original columns plus a symptom_category column.
```

> **Talk track**: "AI_CLASSIFY reads each complaint and assigns the best-matching symptom category. No training data, no fine-tuning — it just works."

**TIMING**: ~1-3 minutes (600 AI_CLASSIFY calls).

**RESULT**: SILVER.WARRANTY_CLAIMS — 600 rows + SYMPTOM_CATEGORY.

---

### Step 6: Classify Failed Sub-Parts

**WHY**: The key enrichment step. Each warranty claim doesn't say WHICH sub-part failed. AI_CLASSIFY reads the technician_notes and determines the failed component from the 7 possible sub-parts for that part type.

**PROMPT**:

```
For each claim in COCO_WORKSHOP.SILVER.WARRANTY_CLAIMS, classify which sub-part failed based on technician_notes. Use the distinct sub_parts from COCO_WORKSHOP.GOLD.PARTS for that claim's part_number as categories. Focus on root cause — the component that failed, not downstream effects. Save as COCO_WORKSHOP.GOLD.WARRANTY_CLAIMS with a failed_sub_part column.
```

> **Talk track**: "This is the magic moment. The AI reads each technician's repair notes and figures out which sub-component actually failed. Now we can trace failures back to specific suppliers and batches."

**TIMING**: ~2-5 minutes (longest step).

**RESULT**: GOLD.WARRANTY_CLAIMS — 600 rows + FAILED_SUB_PART.

---

## ACT 3: Semantic View & Agent Assembly

### Step 7: Create the Semantic View

**WHY**: A semantic view tells Cortex Analyst how to translate natural language questions into SQL — table relationships, metrics, and column meanings.

**PROMPT**:

```
/semantic_studio Create a semantic view called COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS over COCO_WORKSHOP.GOLD.WARRANTY_CLAIMS, COCO_WORKSHOP.GOLD.PARTS, and COCO_WORKSHOP.GOLD.SUPPLIERS. WARRANTY_CLAIMS joins to PARTS on SERIAL_NUMBER and FAILED_SUB_PART = SUB_PART. PARTS joins to SUPPLIERS on SUPPLIER_ID. Include PART_NUMBER as a dimension on both WARRANTY_CLAIMS and PARTS. Include a UNIT_COUNT metric as COUNT(DISTINCT PARTS.SERIAL_NUMBER). Add synonyms: 'vendor' = COMPANY_NAME, 'component' = SUB_PART.
```

> **Talk track**: "The semantic view is the bridge between natural language and SQL. I'm defining table relationships, metrics, and hints — pure SQL DDL, no YAML files."

**RESULT**: Semantic view COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS.

---

### Step 8: Create Cortex Search Service

**WHY**: Index the 5 PDF parts manuals so the agent can answer document questions alongside data questions.

**PROMPT**:

```
Create a Cortex Search Service called COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH over the PDFs in @COCO_WORKSHOP.BRONZE.DOCS. Parse and chunk them first into COCO_WORKSHOP.BRONZE.DOCS_EMBEDDINGS.
```

> **Talk track**: "One prompt — CoCo parses the PDFs, chunks the text, and creates a searchable index. Now the AI can look up torque specs and procedures directly from the source documents."

**If CoCo stalls**, split into two prompts:

> ```
> Parse the 5 PDF files from @COCO_WORKSHOP.BRONZE.DOCS and chunk the text into ~500 token rows. Save to COCO_WORKSHOP.BRONZE.DOCS_EMBEDDINGS with columns: file_name, chunk_index, chunk_text.
> ```
> Then:
> ```
> Create a Cortex Search Service called COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH on the chunk_text column of COCO_WORKSHOP.BRONZE.DOCS_EMBEDDINGS.
> ```

**RESULT**: GOLD.PARTS_MANUAL_SEARCH (active Cortex Search Service).

---

### Step 9: Create the Cortex Agent (Grand Finale)

**WHY**: A Cortex Agent combines structured analytics (semantic view) with document search into one conversational interface.

**PROMPT**:

```
Create a Cortex Agent called COCO_WORKSHOP.GOLD.WARRANTY_AGENT that combines the COCO_WORKSHOP.GOLD.PARTS_MANUAL_SEARCH search service and the COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS semantic view. Use warehouse COCO_WORKSHOP_WH. In the agent instructions, specify that all questions about failure rates, claims, parts, or suppliers must use the WARRANTY_ANALYTICS semantic view tool.
```

> **Talk track**: "One prompt. We just built an AI agent that combines structured data analytics with document search. No API integration, no RAG framework — just declare the tools and Snowflake handles the orchestration."

**RESULT**: GOLD.WARRANTY_AGENT — Cortex Agent with two tools.

---

## Testing the Agent

After the agent is created, test with these 4 questions. The flow tells a story: big picture → drill-down → root cause → documents.

### Q1: The Heat Map

```
Show me the parent part failure rates by symptom description in a heat map
```

> **What it shows**: AI_CLASSIFY enrichment (SYMPTOM_CATEGORY) combined with multi-table join. Proves unstructured complaints became a queryable dimension.

### Q2: Top Failures Drill-Down

```
Show me the top 5 failure rates for all parts, sub-parts, and vendors, grouped in that order in descending order
```

> **What it shows**: Three-table join with UNIT_COUNT-based failure rate. All three data stories surface: Piston and Cylinder Kit (design problem — all 3 vendors at similar rates), VGT Actuator (bad batch from Precision Dynamics), and Main PCB (bad supplier NovaTech).

> **Expected results**:
>
> | # | Part | Sub-Part | Vendor | Claims | Units | Failure Rate |
> |---|------|----------|--------|--------|-------|--------------|
> | 1 | ACM-2800 | Piston and Cylinder Kit | Heartland Steel Fabrication | 49 | 1,305 | 3.75% |
> | 2 | TC-5000 | VGT Actuator | Precision Dynamics Llc | 59 | 2,014 | 2.93% |
> | 3 | TCM-3200 | Main PCB | Novatech Electronics, Llc | 58 | 1,988 | 2.92% |
> | 4 | ACM-2800 | Piston and Cylinder Kit | Great Lakes Castings Corp | 49 | 1,717 | 2.85% |
> | 5 | ACM-2800 | Piston and Cylinder Kit | Midwest Pneumatics, Inc. | 52 | 1,978 | 2.63% |

> **If results show 100% failure rates** — add a Verified Query:
>
> ```
> /semantic_studio Add a verified query to COCO_WORKSHOP.GOLD.WARRANTY_ANALYTICS for the question "Show me the top 5 failure rates for all parts, sub-parts, and vendors, grouped in that order in descending order". The SQL should compute UNIT_COUNT as COUNT(DISTINCT SERIAL_NUMBER) from PARTS grouped by PART_NUMBER and SUB_PART in a CTE, then count claims joined to PARTS and SUPPLIERS, then calculate failure_rate as claim_count / unit_count, ORDER BY failure_rate DESC LIMIT 5.
> ```

### Q3: Root Cause Analysis (Bad Supplier vs Bad Batch)

```
Evaluate failures for Main PCB and VGT Actuator sub parts down to the vendor and batch level to determine if the issues appear to be more of a vendor problem or a batch problem.
```

> **What it shows**: The agent reasons about two failure patterns:
> - **Main PCB**: NovaTech has elevated failure rate, others near zero. All batches affected → bad supplier.
> - **VGT Actuator**: Precision Dynamics elevated, but batch B-2024-PD-VA-07 is the outlier → bad batch.

### Q4: Cross-Tool — Data + Docs (The Wow Moment)

```
What are possible cascading effects of a Main PCB going out in a TCM-3200?
```

> **What it shows**: The search tool fires for the first time. The agent pulls from the TCM-3200 parts manual to explain how a Main PCB failure cascades to other sub-components. Demonstrates reasoning across structured data AND unstructured documents in one answer.

---

## Quick Reference: What Each AI Function Does

| Function | What It Does | Where We Use It |
|----------|-------------|-----------------|
| **AI_SUMMARIZE_AGG** | Aggregates and summarizes multiple text values into one paragraph | Step 3: Summarize 600 complaints into 5 part-level summaries |
| **COMPLETE** (llama3.1-70b) | General-purpose LLM for text generation and reasoning | Step 4b: Select 10 best symptom categories from 20 candidates |
| **AI_CLASSIFY** | Classifies text into one of N provided categories | Step 5: Tag complaints with symptom categories. Step 6: Identify failed sub-parts. |
| **AI_PARSE_DOCUMENT** | Extracts text content from PDF/image files on a stage | Step 8a: Parse parts manual PDFs into searchable text chunks |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| AI_CLASSIFY returns empty strings | Add `task_description` to the config object |
| AI_CLASSIFY JSON path wrong | Extract with `['labels'][0]::VARCHAR`, NOT `:label::VARCHAR` |
| AI_SUMMARIZE_AGG unknown function | Use without the `SNOWFLAKE.CORTEX.` schema prefix |
| Semantic view creation fails | Ensure PRIMARY KEY is defined on referenced table's join columns |
| COMPLETE returns malformed output | Specify model: `SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', prompt)` |
| Semantic view has 0 metrics | Use full aggregate expressions (e.g., `COUNT(TABLE.COL)`) |
| Agent "Analyst tool missing execution environment" | Edit agent in Snowsight → add COCO_WORKSHOP_WH to the semantic view tool's execution settings |
| Q2 returns 100% failure rates | The agent isn't using the semantic view properly. Add a VQR (see Q2 fallback above) |

---

## Cleanup

```sql
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
```
