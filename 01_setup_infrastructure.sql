-- ============================================================================
-- SCRIPT 01: INFRASTRUCTURE INITIALIZATION (TRIAL ACCOUNT COMPATIBLE)
-- Description: Builds core database structures and staging area.
-- ============================================================================

-- 1. Create and select the project database
CREATE OR REPLACE DATABASE video_intelligence_db;
USE DATABASE video_intelligence_db;

-- 2. Create and select the target schema
CREATE OR REPLACE SCHEMA public;
USE SCHEMA public;

-- 3. Create an internal stage folder to receive local audio chunk PUT uploads
CREATE OR REPLACE STAGE media_stage
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- 4. Create the target Vector Search Index table
CREATE OR REPLACE TABLE fct_video_search_index (
    video_name VARCHAR(500),
    chunk_id VARCHAR(50),
    chunk_seconds_offset FLOAT,         -- Tracks the 15-min shift multiplier (0, 900, 1800, etc.)
    segment_start_time FLOAT,           -- The relative second inside the 15-min chunk
    global_start_timestamp FLOAT,       -- The REAL second in the movie (Offset + Segment Start)
    spoken_text STRING,                 -- Holds the transcription string
    text_vector_embedding VECTOR(FLOAT, 768)  -- Holds the 768-dimensional semantic coordinates
);