import os
import subprocess
import re
from pathlib import Path
import whisper
from sentence_transformers import SentenceTransformer
from config import CHUNK_DIR, get_snowflake_connection

# 🧠 Initializing AI Models locally in system memory
print("🎙️ Loading OpenAI Whisper Transcription engine (base model)...")
whisper_model = whisper.load_model("base")

print("🧠 Loading Sentence Transformer vector model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def upload_chunks_to_snowflake(video_name: str, raw_audio_path: Path):
    """
    Transcribes the full audio stream via OpenAI Whisper to completely protect word splits.
    Implements a rolling 15-minute semantic sliding window with a 1-minute overlap buffer,
    then pushes high-resolution sentence vector records to Snowflake storage.
    """
    print(f"❄️ Connecting to Snowflake database clusters for tracking: {video_name}...")
    
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        print("✅ Connection to Snowflake established successfully!")

        # 1. RUN OPENAI WHISPER ON THE WHOLE AUDIO FILE
        print(f"🔊 Processing audio signals. Whisper transcribing full timeline: {raw_audio_path.name}...")
        whisper_result = whisper_model.transcribe(str(raw_audio_path))
        whisper_segments = whisper_result.get("segments", [])
        
        print(f"🧩 Whisper generated {len(whisper_segments)} structural speech sentences.")
        
        WINDOW_DURATION = 900.0  # 15 minutes macro blocks
        OVERLAP_BUFFER = 60.0    # 1 minute of trailing context overlap
        
        # Calculate how many 15-minute macro blocks we need to map based on full audio length
        total_duration = whisper_result.get("org_dict", {}).get("duration", 0.0)
        if not total_duration and whisper_segments:
            total_duration = whisper_segments[-1].get("end", WINDOW_DURATION)
            
        num_windows = max(1, int(total_duration // WINDOW_DURATION) + 1)
        print(f"📐 Rolling timeline spans {round(total_duration/60, 2)} minutes. Indexing across {num_windows} macro blocks...")

        rows_inserted_count = 0

        # 2. THE SLIDING WINDOW LOOP (Handles your boundary edge case)
        for i in range(num_windows):
            # Calculate the boundaries for this specific macro window block
            window_start = i * WINDOW_DURATION
            window_end = window_start + WINDOW_DURATION
            
            # Stretch the end of this window out by 1 minute to capture trailing border text
            extended_window_end = window_end + OVERLAP_BUFFER
            
            chunk_id = f"block_{i:03d}"
            print(f"\n--- 📦 Populating Window: {chunk_id} [{int(window_start/60)}m to {int(window_end/60)}m + Overlap] ---")

            # Gather any sentences that talk within this time range
            for seg in whisper_segments:
                seg_start = float(seg.get("start", 0.0))
                
                # Check if this sentence lands inside our current active window block bounds
                if window_start <= seg_start < extended_window_end:
                    spoken_text = seg.get("text", "").strip()
                    
                    if not spoken_text or spoken_text == ".":
                        continue
                    
                    # Generate the precise vector embedding for just this small sentence
                    vector_embedding = embedding_model.encode(spoken_text).tolist()

                    insert_query = """
                        INSERT INTO fct_video_search_index (
                            video_name, chunk_id, chunk_seconds_offset, 
                            segment_start_time, global_start_timestamp, 
                            spoken_text, text_vector_embedding
                        ) 
                        SELECT 
                            v.col1, v.col2, v.col3, v.col4, v.col5, v.col6, 
                            PARSE_JSON(v.col7)::VECTOR(FLOAT, 384)
                        FROM VALUES (%s, %s, %s, %s, %s, %s, %s) AS v(col1, col2, col3, col4, col5, col6, col7);
                    """
                    
                    cursor.execute(insert_query, (
                        video_name, chunk_id, float(window_start),
                        seg_start - window_start, seg_start, spoken_text, str(vector_embedding)
                    ))
                    
                    rows_inserted_count += 1

            print(f"✅ Window {chunk_id} indexing complete.")

        # 3. TRANSACTION FINALIZATION
        print(f"\n💾 Attempting to COMMIT {rows_inserted_count} context-linked rows to Snowflake...")
        conn.commit()
        print("🎉 Database TRANSACTION COMMITTED successfully!")

        # 4. DISK DISPOSAL CLEANUP
        try:
            if raw_audio_path.exists():
                os.remove(raw_audio_path)
                print(f"🗑️ Cleaned up temp macro audio track: {raw_audio_path.name}")
        except Exception as e:
            print(f"⚠️ Warning: Audio track cache cleanup skipped: {e}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Critical Snowflake Pipeline Error: {str(e)}")


def split_video_audio_to_chunks(video_path: Path, video_name: str):
    """
    Extracts a singular clean, un-sliced audio track from the uploaded video.
    Delegates timeline slicing straight to Python's sliding text window matrix.
    """
    print(f"\n🎬 Initiating media preprocessing sequence for: {video_name}")
    
    # We create a single parent audio file instead of cutting it with ffmpeg's chunker
    output_audio_track = CHUNK_DIR / f"{video_name}_full_audio.mp3"
    
    ffmpeg_command = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-map", "a",
        "-codec:a", "libmp3lame",
        "-q:a", "2",
        str(output_audio_track)
    ]
    
    try:
        print("⚡ Extracting core audio tracks via FFmpeg...")
        subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("✅ Core audio extraction completed successfully.")
        
        # Pass the single audio track over to our smart sliding window processor
        upload_chunks_to_snowflake(video_name, output_audio_track)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Critical FFmpeg processing failure code: {e.returncode}")
        print(f"Stderr context: {e.stderr}")


def search_video_index(db_connection, search_query: str):
    """
    Performs true Vector Semantic Search using Snowflake Vector Cosine Similarity math functions.
    """
    query_vector = embedding_model.encode(search_query).tolist()
    cursor = db_connection.cursor()
    try:
        sql_query = """
            SELECT video_name, global_start_timestamp, spoken_text,
                   VECTOR_COSINE_SIMILARITY(text_vector_embedding, PARSE_JSON(%s)::VECTOR(FLOAT, 384)) as similarity
            FROM fct_video_search_index
            ORDER BY similarity DESC
            LIMIT 5;
        """
        cursor.execute(sql_query, (str(query_vector),))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "video_name": row[0],
                "timestamp_seconds": row[1],
                "matched_text": row[2],
                "confidence_score": round(float(row[3]), 4)
            })
        return results
    finally:
        cursor.close()