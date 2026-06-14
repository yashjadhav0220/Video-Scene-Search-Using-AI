import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import your custom configurations and pipeline orchestration modules
from config import get_snowflake_connection, VIDEO_DIR
from services import split_video_audio_to_chunks, search_video_index

app = FastAPI(
    title="AI Video Semantic Search Engine",
    description="FastAPI orchestration framework handling video chunks processing via Snowflake Cortex AI vectors.",
    version="1.0.0"
)

app.mount("/images", StaticFiles(directory="images"), name="images")

# 🌐 Enable Cross-Origin Resource Sharing (CORS) for local frontend routing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🛠️ Satisfy automated browser favicon requests cleanly to keep server logs clean
@app.get("/favicon.ico", include_in_schema=False)
def get_favicon():
    """Returns an empty 204 No Content status to satisfy automated browser requests."""
    return Response(status_code=204)


# 🎬 HIGH-PERFORMANCE STREAMING ROUTER WITH DIAGNOSTIC LOGGING
@app.get("/static/videos/{video_name}")
def get_video_stream(video_name: str, response: Response):
    """
    Delivers the video asset while explicitly signaling 'Accept-Ranges' to the 
    browser engine. This forces Chrome/Edge to unlock timeline seeking.
    """
    video_path = VIDEO_DIR / video_name
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Requested media asset missing.")

    file_size = video_path.stat().st_size
    
    # 🌟 CRITICAL: Explicitly tell Chrome's multimedia layer that this file can be sliced
    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Content-Type"] = "video/mp4"
    
    # Open and stream the file cleanly
    with open(video_path, "rb") as video_file:
        data = video_file.read()
        
    print(f"\n🚀 [SERVER STREAM] Explicit Accept-Ranges header delivered for: {video_name} ({file_size} bytes)")
    
    return Response(
        content=data,
        status_code=200,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Disposition": f'inline; filename="{video_name}"'
        },
        media_type="video/mp4"
    )


# 🖥️ ROUTE 1: Render the Primary UI Layout Template
@app.get("/")
def read_root():
    ui_path = Path("templates/index.html")
    if not ui_path.exists():
        raise HTTPException(status_code=404, detail="Frontend interface layout 'templates/index.html' not found.")
    return FileResponse(str(ui_path))


# 🚀 ROUTE 2: Handle Video Ingestion & Synchronous AI Processing Pipeline
@app.post("/api/upload")
def upload_video_stream(file: UploadFile = File(...)):
    if not file.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid media type. Only standard .mp4 containers are supported.")

    clean_filename = os.path.basename(file.filename).replace(" ", "_")
    saved_video_path = VIDEO_DIR / clean_filename

    try:
        with saved_video_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📁 Video written to local disk: {saved_video_path.name}")

        print("⏳ [PIPELINE] Initiating synchronous processing engine...")
        print("⏳ [PIPELINE] Extracting audio segments and executing Snowflake database transactions...")
        
        # 🌟 CHANGE: Called directly without BackgroundTasks so the response waits for completion
        split_video_audio_to_chunks(saved_video_path, clean_filename)
        
        print("✅ [PIPELINE] Database synchronization complete.")

        return {
            "status": "success",
            "message": "Video successfully uploaded and database transaction fully completed.",
            "file_name": clean_filename
        }

    except Exception as e:
        if saved_video_path.exists():
            os.remove(saved_video_path)
        print(f"❌ [PIPELINE ERROR] Critical ingestion breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Critical ingestion breakdown: {str(e)}")


# 🔍 ROUTE 3: Compute Vector Similarities & Fetch Context Coordinates
@app.get("/api/search")
def search_semantic_index(query: str):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search parameters cannot be blank.")

    try:
        db_conn = get_snowflake_connection()
        search_results = search_video_index(db_conn, query)
        db_conn.close()

        return {
            "query": query,
            "total_matches": len(search_results),
            "results": search_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database similarity query failure: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # explicitly running on local standard port loop
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)