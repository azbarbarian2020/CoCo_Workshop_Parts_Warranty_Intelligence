-- ============================================================================
-- CoCo Workshop: Pre-Demo Setup
-- Run this ONCE on a fresh account to create infrastructure and load Bronze.
-- The audience never sees this script.
-- ============================================================================
--
-- BEFORE RUNNING THIS SCRIPT:
--   1. Upload CSV files to stages using Snow CLI:
--        snow stage copy data/suppliers.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
--        snow stage copy data/parts.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
--        snow stage copy data/warranty_claims.csv @COCO_WORKSHOP.BRONZE.DATA_STAGE --overwrite
--   2. Upload PDF manuals:
--        snow stage copy docs/PM_*.pdf @COCO_WORKSHOP.BRONZE.DOCS --overwrite
--   3. Then run this script to create tables and load data.
--
-- NOTE: The stage CREATE statements must run first so the stages exist before
-- you upload files. Run Sections 1-2 first, upload files, then run Sections 3-5.
-- ============================================================================

-- ============================================================================
-- 1. DATABASE, SCHEMAS, WAREHOUSE
-- ============================================================================
CREATE DATABASE IF NOT EXISTS COCO_WORKSHOP;
USE DATABASE COCO_WORKSHOP;

CREATE WAREHOUSE IF NOT EXISTS COCO_WORKSHOP_WH
  GENERATION = '2'
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'CoCo Workshop: Parts Warranty Intelligence';
USE WAREHOUSE COCO_WORKSHOP_WH;

CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS GOLD;

-- ============================================================================
-- 2. STAGES
-- ============================================================================
CREATE STAGE IF NOT EXISTS BRONZE.DATA_STAGE;

CREATE STAGE IF NOT EXISTS BRONZE.DOCS
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- ============================================================================
-- 3. BRONZE TABLES
-- ============================================================================
CREATE OR REPLACE TABLE BRONZE.SUPPLIER_RAW (
    SUPPLIER_ID VARCHAR,
    COMPANY_NAME VARCHAR,
    CONTACT_NAME VARCHAR,
    PHONE VARCHAR,
    EMAIL VARCHAR,
    ADDRESS VARCHAR,
    CITY VARCHAR,
    STATE VARCHAR,
    ZIP VARCHAR,
    COUNTRY VARCHAR,
    CERTIFICATION VARCHAR
);

CREATE OR REPLACE TABLE BRONZE.PARTS_RAW (
    SERIAL_NUMBER VARCHAR,
    PART_NUMBER VARCHAR,
    PART_DESCRIPTION VARCHAR,
    MANUFACTURE_DATE VARCHAR,
    BOM VARCHAR
);

CREATE OR REPLACE TABLE BRONZE.WARRANTY_CLAIMS_RAW (
    CLAIM_ID VARCHAR,
    SERIAL_NUMBER VARCHAR,
    PART_NUMBER VARCHAR,
    CLAIM_DATE VARCHAR,
    MILEAGE NUMBER,
    DEALER_ID VARCHAR,
    CUSTOMER_COMPLAINT VARCHAR,
    TECHNICIAN_NOTES VARCHAR
);

-- ============================================================================
-- 4. LOAD CSVs FROM STAGE
-- ============================================================================
COPY INTO BRONZE.SUPPLIER_RAW
FROM @BRONZE.DATA_STAGE/suppliers.csv
FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"' EMPTY_FIELD_AS_NULL = TRUE)
ON_ERROR = 'CONTINUE';

COPY INTO BRONZE.PARTS_RAW
FROM @BRONZE.DATA_STAGE/parts.csv
FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"' EMPTY_FIELD_AS_NULL = TRUE)
ON_ERROR = 'CONTINUE';

COPY INTO BRONZE.WARRANTY_CLAIMS_RAW
FROM @BRONZE.DATA_STAGE/warranty_claims.csv
FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"' EMPTY_FIELD_AS_NULL = TRUE)
ON_ERROR = 'CONTINUE';

-- ============================================================================
-- 5. REFRESH DOCS STAGE & VERIFY
-- ============================================================================
ALTER STAGE BRONZE.DOCS REFRESH;

SELECT 'SUPPLIER_RAW' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM BRONZE.SUPPLIER_RAW
UNION ALL SELECT 'PARTS_RAW', COUNT(*) FROM BRONZE.PARTS_RAW
UNION ALL SELECT 'WARRANTY_CLAIMS_RAW', COUNT(*) FROM BRONZE.WARRANTY_CLAIMS_RAW;
-- Expected: 12, 25000, 500

SELECT * FROM DIRECTORY(@BRONZE.DOCS);
-- Expected: 5 PDF files
