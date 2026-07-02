-- ============================================================================
-- CoCo Workshop: Pre-Demo Setup (Multi-User Version)
-- Run this ONCE on a fresh account to create infrastructure and load Bronze.
-- The audience never sees this script.
-- ============================================================================
--
-- This version prefixes the database name with the current username so multiple
-- users can run the workshop simultaneously on the same account.
--
-- Source repo: https://github.com/azbarbarian2020/CoCo_Workshop_Parts_Warranty_Intelligence
-- ============================================================================

-- ============================================================================
-- 1. DATABASE, SCHEMAS, WAREHOUSE
-- ============================================================================
SET MY_USER = CURRENT_USER();
SET DB_NAME = (SELECT $MY_USER || '_COCO_WORKSHOP');
SET WH_NAME = (SELECT $MY_USER || '_COCO_WORKSHOP_WH');

CREATE DATABASE IF NOT EXISTS IDENTIFIER($DB_NAME);
USE DATABASE IDENTIFIER($DB_NAME);

CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($WH_NAME)
  GENERATION = '2'
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'CoCo Workshop: Parts Warranty Intelligence';
USE WAREHOUSE IDENTIFIER($WH_NAME);

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
-- 3. GIT REPOSITORY INTEGRATION (pulls data/docs from GitHub)
-- ============================================================================
CREATE OR REPLACE API INTEGRATION GIT_API_INTEGRATION_COCO
  API_PROVIDER = GIT_HTTPS_API
  API_ALLOWED_PREFIXES = ('https://github.com/azbarbarian2020/')
  ENABLED = TRUE;

CREATE OR REPLACE GIT REPOSITORY BRONZE.WORKSHOP_REPO
  API_INTEGRATION = GIT_API_INTEGRATION_COCO
  ORIGIN = 'https://github.com/azbarbarian2020/CoCo_Workshop_Parts_Warranty_Intelligence.git';

ALTER GIT REPOSITORY BRONZE.WORKSHOP_REPO FETCH;

-- ============================================================================
-- 4. COPY FILES FROM GIT REPO TO STAGES
-- ============================================================================
COPY FILES
  INTO @BRONZE.DATA_STAGE
  FROM @BRONZE.WORKSHOP_REPO/branches/main/data/
  FILES = ('suppliers.csv', 'parts.csv', 'warranty_claims.csv');

COPY FILES
  INTO @BRONZE.DOCS
  FROM @BRONZE.WORKSHOP_REPO/branches/main/docs/
  FILES = ('PM_TC-5000_Turbocharger_Assembly.pdf',
           'PM_TCM-3200_Transmission_Control_Module.pdf',
           'PM_EXM-4100_Exhaust_Manifold_Assembly.pdf',
           'PM_ACM-2800_Air_Compressor_Assembly.pdf',
           'PM_SGB-6500_Steering_Gear_Box.pdf');

-- ============================================================================
-- 5. BRONZE TABLES
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
-- 6. LOAD CSVs FROM STAGE
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
-- 7. REFRESH DOCS STAGE & VERIFY
-- ============================================================================
ALTER STAGE BRONZE.DOCS REFRESH;

SELECT 'SUPPLIER_RAW' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM BRONZE.SUPPLIER_RAW
UNION ALL SELECT 'PARTS_RAW', COUNT(*) FROM BRONZE.PARTS_RAW
UNION ALL SELECT 'WARRANTY_CLAIMS_RAW', COUNT(*) FROM BRONZE.WARRANTY_CLAIMS_RAW;
-- Expected: 12, 25000, 600

SELECT * FROM DIRECTORY(@BRONZE.DOCS);
-- Expected: 5 PDF files

-- ============================================================================
-- REMINDER: Tell CoCo your database and warehouse names at Step 0:
--   Use database <YOUR_USER>_COCO_WORKSHOP and warehouse <YOUR_USER>_COCO_WORKSHOP_WH
-- ============================================================================
SELECT 'Setup complete! Your database: ' || $DB_NAME || ', warehouse: ' || $WH_NAME AS STATUS;
