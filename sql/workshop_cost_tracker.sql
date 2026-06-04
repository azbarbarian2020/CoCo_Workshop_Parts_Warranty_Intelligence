-- ============================================================================
-- CoCo Workshop: Total Cost Tracker
-- Run this AFTER completing the workshop to see all costs incurred.
-- Requires: ACCOUNTADMIN role (for ACCOUNT_USAGE views)
-- Note: ACCOUNT_USAGE views have up to 3 hours of latency.
-- ============================================================================

USE ROLE ACCOUNTADMIN;
ALTER SESSION SET TIMEZONE = 'America/Los_Angeles';

-- ============================================================================
-- STEP 1 (before workshop): Run SELECT CURRENT_TIMESTAMP(); and save it.
-- STEP 2 (after workshop):  Run SELECT CURRENT_TIMESTAMP(); again.
-- STEP 3: Paste both values below (local time, no UTC conversion needed).
-- STEP 4: Wait 3+ hours for ACCOUNT_USAGE views to populate, then run.
--
-- IMPORTANT: Some views (AISQL, WAREHOUSE_METERING) aggregate to the hour.
-- The script automatically pads the start time down to the hour boundary
-- so no data is missed.
-- ============================================================================
SET START_TS_RAW = '2026-05-11 15:34:00'::TIMESTAMP_LTZ;
SET END_TS_RAW   = '2026-05-11 16:55:00'::TIMESTAMP_LTZ;

SET START_TS = DATE_TRUNC('HOUR', $START_TS_RAW);
SET END_TS   = DATEADD('HOUR', 1, DATE_TRUNC('HOUR', $END_TS_RAW));

-- ============================================================================
-- 1. WAREHOUSE COMPUTE CREDITS (COCO_WORKSHOP_WH)
-- ============================================================================
SELECT
    '1. WAREHOUSE COMPUTE' AS COST_CATEGORY,
    ROUND(SUM(CREDITS_USED), 6) AS CREDITS_USED,
    ROUND(SUM(CREDITS_USED_COMPUTE), 6) AS CREDITS_COMPUTE,
    ROUND(SUM(CREDITS_USED_CLOUD_SERVICES), 6) AS CREDITS_CLOUD_SERVICES
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE WAREHOUSE_NAME = 'COCO_WORKSHOP_WH'
  AND START_TIME < $END_TS
  AND END_TIME   > $START_TS;

-- ============================================================================
-- 2. CORTEX AI SQL FUNCTIONS (AI_CLASSIFY, AI_COMPLETE, AI_SUMMARIZE, etc.)
--    USAGE_TIME is hour-truncated. We join to QUERY_HISTORY to filter by
--    COCO_WORKSHOP database or COCO_WORKSHOP_WH warehouse.
-- ============================================================================
SELECT
    '2. CORTEX AI SQL FUNCTIONS' AS COST_CATEGORY,
    a.FUNCTION_NAME,
    a.MODEL_NAME,
    COUNT(DISTINCT a.QUERY_ID) AS QUERY_COUNT,
    SUM(a.TOKENS) AS TOTAL_TOKENS,
    ROUND(SUM(a.TOKEN_CREDITS), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AISQL_USAGE_HISTORY a
JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
  ON a.QUERY_ID = q.QUERY_ID
WHERE a.USAGE_TIME >= $START_TS
  AND a.USAGE_TIME <  $END_TS
  AND (q.DATABASE_NAME = 'COCO_WORKSHOP' OR q.WAREHOUSE_NAME = 'COCO_WORKSHOP_WH')
GROUP BY a.FUNCTION_NAME, a.MODEL_NAME
ORDER BY TOTAL_CREDITS DESC;

-- ============================================================================
-- 3. CORTEX SEARCH SERVICE (serving credits for search within COCO_WORKSHOP)
-- ============================================================================
SELECT
    '3. CORTEX SEARCH' AS COST_CATEGORY,
    SERVICE_NAME,
    CONSUMPTION_TYPE,
    ROUND(SUM(CREDITS), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
WHERE DATABASE_NAME = 'COCO_WORKSHOP'
  AND USAGE_DATE >= $START_TS::DATE
  AND USAGE_DATE <= $END_TS::DATE
GROUP BY SERVICE_NAME, CONSUMPTION_TYPE
ORDER BY TOTAL_CREDITS DESC;

-- ============================================================================
-- 4. CORTEX ANALYST (semantic view queries)
--    This view has no database column. When Analyst is invoked through a
--    Cortex Agent, credits appear in Section 5 instead of here.
--    On a fresh account this captures any standalone Analyst calls.
-- ============================================================================
SELECT
    '4. CORTEX ANALYST' AS COST_CATEGORY,
    USERNAME,
    SUM(REQUEST_COUNT) AS TOTAL_REQUESTS,
    ROUND(SUM(CREDITS), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
WHERE START_TIME >= $START_TS
  AND START_TIME <  $END_TS
GROUP BY USERNAME
ORDER BY TOTAL_CREDITS DESC;

-- ============================================================================
-- 5. CORTEX AGENT (all tool costs subsumed here: Analyst, Search, LLM)
-- ============================================================================
SELECT
    '5. CORTEX AGENT' AS COST_CATEGORY,
    AGENT_NAME,
    COUNT(*) AS REQUEST_COUNT,
    SUM(TOKENS) AS TOTAL_TOKENS,
    ROUND(SUM(TOKEN_CREDITS), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
WHERE START_TIME >= $START_TS
  AND START_TIME <  $END_TS
  AND AGENT_DATABASE_NAME = 'COCO_WORKSHOP'
GROUP BY AGENT_NAME
ORDER BY TOTAL_CREDITS DESC;

-- ============================================================================
-- 6. DOCUMENT PROCESSING (AI_PARSE_DOCUMENT for PDFs)
--    NOTE: AI_PARSE_DOCUMENT called via direct SQL shows in AISQL (Section 2),
--    not here. This section captures Document AI / Build Model usage only.
-- ============================================================================
SELECT
    '6. DOCUMENT PROCESSING' AS COST_CATEGORY,
    d.FUNCTION_NAME,
    COUNT(DISTINCT d.QUERY_ID) AS QUERY_COUNT,
    SUM(d.PAGE_COUNT) AS TOTAL_PAGES,
    ROUND(SUM(d.CREDITS_USED), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY d
JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
  ON d.QUERY_ID = q.QUERY_ID
WHERE d.START_TIME >= $START_TS
  AND d.START_TIME <  $END_TS
  AND (q.DATABASE_NAME = 'COCO_WORKSHOP' OR q.WAREHOUSE_NAME = 'COCO_WORKSHOP_WH')
GROUP BY d.FUNCTION_NAME
ORDER BY TOTAL_CREDITS DESC;

-- ============================================================================
-- 7. CORTEX CODE IN SNOWSIGHT (CoCo prompts during the workshop)
--    No database filter available; on a fresh account this IS workshop usage.
-- ============================================================================
SELECT
    '7. CORTEX CODE SNOWSIGHT (SUMMARY)' AS COST_CATEGORY,
    COUNT(*) AS TOTAL_REQUESTS,
    SUM(TOKENS) AS TOTAL_TOKENS,
    ROUND(SUM(TOKEN_CREDITS), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
WHERE USAGE_TIME >= $START_TS
  AND USAGE_TIME <  $END_TS;

SELECT
    '7b. COCO SNOWSIGHT BY MODEL' AS COST_CATEGORY,
    f.KEY AS MODEL_NAME,
    SUM(f.VALUE:input::NUMBER) AS INPUT_TOKENS,
    SUM(f.VALUE:output::NUMBER) AS OUTPUT_TOKENS,
    SUM(COALESCE(f.VALUE:cache_read_input::NUMBER, 0)) AS CACHE_READ_TOKENS,
    COUNT(*) AS REQUEST_COUNT
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY,
     LATERAL FLATTEN(input => TOKENS_GRANULAR) f
WHERE USAGE_TIME >= $START_TS
  AND USAGE_TIME <  $END_TS
GROUP BY f.KEY
ORDER BY INPUT_TOKENS DESC;

-- ============================================================================
-- 8. CROSS-CHECK: METERING_HISTORY (authoritative credit totals)
-- ============================================================================
SELECT
    '8. METERING HISTORY' AS COST_CATEGORY,
    SERVICE_TYPE,
    NAME,
    ROUND(SUM(CREDITS_USED), 6) AS TOTAL_CREDITS
FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY
WHERE START_TIME < $END_TS
  AND END_TIME   > $START_TS
  AND (   SERVICE_TYPE IN ('AI_SERVICES','CORTEX_AGENTS','CORTEX_CODE_SNOWSIGHT','SNOWFLAKE_INTELLIGENCE')
       OR (SERVICE_TYPE = 'WAREHOUSE_METERING' AND NAME = 'COCO_WORKSHOP_WH')
      )
GROUP BY SERVICE_TYPE, NAME
ORDER BY TOTAL_CREDITS DESC;

-- ============================================================================
-- 9. GRAND TOTAL
-- ============================================================================
WITH warehouse_costs AS (
    SELECT COALESCE(SUM(CREDITS_USED), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
    WHERE WAREHOUSE_NAME = 'COCO_WORKSHOP_WH'
      AND START_TIME < $END_TS AND END_TIME > $START_TS
),
aisql_costs AS (
    SELECT COALESCE(SUM(a.TOKEN_CREDITS), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AISQL_USAGE_HISTORY a
    JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON a.QUERY_ID = q.QUERY_ID
    WHERE a.USAGE_TIME >= $START_TS AND a.USAGE_TIME < $END_TS
      AND (q.DATABASE_NAME = 'COCO_WORKSHOP' OR q.WAREHOUSE_NAME = 'COCO_WORKSHOP_WH')
),
search_costs AS (
    SELECT COALESCE(SUM(CREDITS), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_SEARCH_DAILY_USAGE_HISTORY
    WHERE DATABASE_NAME = 'COCO_WORKSHOP'
      AND USAGE_DATE >= $START_TS::DATE AND USAGE_DATE <= $END_TS::DATE
),
analyst_costs AS (
    SELECT COALESCE(SUM(CREDITS), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_ANALYST_USAGE_HISTORY
    WHERE START_TIME >= $START_TS AND START_TIME < $END_TS
),
agent_costs AS (
    SELECT COALESCE(SUM(TOKEN_CREDITS), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY
    WHERE START_TIME >= $START_TS AND START_TIME < $END_TS
      AND AGENT_DATABASE_NAME = 'COCO_WORKSHOP'
),
docproc_costs AS (
    SELECT COALESCE(SUM(d.CREDITS_USED), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_DOCUMENT_PROCESSING_USAGE_HISTORY d
    JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON d.QUERY_ID = q.QUERY_ID
    WHERE d.START_TIME >= $START_TS AND d.START_TIME < $END_TS
      AND (q.DATABASE_NAME = 'COCO_WORKSHOP' OR q.WAREHOUSE_NAME = 'COCO_WORKSHOP_WH')
),
coco_snowsight_costs AS (
    SELECT COALESCE(SUM(TOKEN_CREDITS), 0) AS credits
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
    WHERE USAGE_TIME >= $START_TS AND USAGE_TIME < $END_TS
)
SELECT
    '--- GRAND TOTAL ---' AS COST_CATEGORY,
    ROUND(w.credits, 6) AS WAREHOUSE_CREDITS,
    ROUND(ai.credits, 6) AS AISQL_CREDITS,
    ROUND(s.credits, 6) AS SEARCH_CREDITS,
    ROUND(an.credits, 6) AS ANALYST_CREDITS,
    ROUND(ag.credits, 6) AS AGENT_CREDITS,
    ROUND(dp.credits, 6) AS DOC_PROCESSING_CREDITS,
    ROUND(cc.credits, 6) AS COCO_SNOWSIGHT_CREDITS,
    ROUND(w.credits + ai.credits + s.credits + an.credits + ag.credits + dp.credits + cc.credits, 6) AS TOTAL_CREDITS
FROM warehouse_costs w,
     aisql_costs ai,
     search_costs s,
     analyst_costs an,
     agent_costs ag,
     docproc_costs dp,
     coco_snowsight_costs cc;
