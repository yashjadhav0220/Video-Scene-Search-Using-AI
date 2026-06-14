-- 1. Create procedure for insertion 
CREATE OR REPLACE PROCEDURE insert_video_segment_record(
    p_video_name STRING,
    p_chunk_id STRING,
    p_chunk_seconds_offset FLOAT,
    p_segment_start_time FLOAT,
    p_global_start_timestamp FLOAT,
    p_spoken_text STRING,
    p_vector_embedding_str STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
    INSERT INTO fct_video_search_index (
        video_name, 
        chunk_id, 
        chunk_seconds_offset, 
        segment_start_time, 
        global_start_timestamp, 
        spoken_text, 
        text_vector_embedding
    ) 
    SELECT 
        :p_video_name, 
        :p_chunk_id, 
        :p_chunk_seconds_offset, 
        :p_segment_start_time, 
        :p_global_start_timestamp, 
        :p_spoken_text, 
        PARSE_JSON(:p_vector_embedding_str)::VECTOR(FLOAT, 384);
        
    RETURN 'SUCCESS';
END;
$$;


-- 2. Getting semantic search
CREATE OR REPLACE PROCEDURE GET_SEMANTIC_VIDEO_MATCHES(
    SEARCH_QUERY VARCHAR,
    TARGET_VIDEO VARCHAR
)
RETURNS TABLE (
    VIDEO_NAME VARCHAR,
    START_TIMESTAMP FLOAT,
    END_TIMESTAMP FLOAT,
    SPOKEN_TEXT VARCHAR,
    MATCH_SCORE FLOAT
)
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    -- Define a dynamic result set cursor to hold our semantic vector query output
    res RESULTSET;
BEGIN
    res := (
        SELECT 
            VIDEO_NAME,
            GLOBAL_START_TIMESTAMP AS START_TIMESTAMP,
            GLOBAL_END_TIMESTAMP AS END_TIMESTAMP,
            SPOKEN_TEXT,
            -- Calculate mathematical closeness between the user query vector and database rows
            VECTOR_COSINE_SIMILARITY(
                SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', :SEARCH_QUERY),
                TEXT_VECTOR_EMBEDDING
            )::FLOAT AS MATCH_SCORE
        FROM FCT_VIDEO_SEARCH_INDEX
        WHERE VIDEO_NAME = :TARGET_VIDEO
          -- Filter out low-confidence random matches to keep search tight
          AND MATCH_SCORE > 0.45 
        ORDER BY MATCH_SCORE DESC
        -- Grab the best matching scene
        LIMIT 1
    );
    
    RETURN TABLE(res);
END;
$$;


-- 3. Create db, warehouses and so on
CREATE DATABASE video_intelligence_db;
USE DATABASE video_intelligence_db;
USE SCHEMA public;


-- Create the new structure matching your local python data shapes
CREATE TABLE fct_video_search_index (
    video_name STRING,
    chunk_id STRING,
    chunk_seconds_offset INT,
    segment_start_time FLOAT,
    global_start_timestamp FLOAT,
    spoken_text STRING,
    text_vector_embedding VECTOR(FLOAT, 384) -- Perfectly matches your local free model
);