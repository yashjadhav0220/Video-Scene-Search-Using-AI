# Video Scene Search Using AI

An AI-powered video processing and retrieval pipeline that extracts audio, transcribes verbal content with precise timecode synchronization, and implements native vector similarity matching directly inside the cloud perimeter. 

This project integrates localized machine learning embedding generation with Snowflake's ultra-high-performance data cloud architecture to deliver sub-second semantic search across video archives.

---

## 🏗️ Architecture & Core Components

The processing loop handles localized video decoupling and distributed cloud vector matching through an isolated multi-tiered layout:

1. **Audio Isolation Layer:** Automatically uncouples localized audio frequencies from incoming video signals (`.mp4`) with surgical chronology preservation using FFmpeg pipelines.
2. **Granular Timeline Extraction:** Maps audio context to automated timestamped sentence arrays to preserve accurate spatial-temporal coordinates.
3. **Semantic Synthesis:** Converts text fragments into a dense 384-dimensional mathematical space using the native `all-MiniLM-L6-v2` transformer model.
4. **Cloud Execution Perimeter:** Streams high-performance NumPy float-arrays sequentially into specialized Snowflake computing structures for optimized cloud-native storage and rapid distance querying.

---

## 🛠️ Prerequisites & System Dependencies

Before setting up the localized Python execution space, your host machine requires the following system-level tools:

* **Python:** Version `3.10` or `3.11` (Stable compilation recommended).
* **FFmpeg:** Required for structural audio extraction.
  * **macOS:** `brew install ffmpeg`
  * **Windows:** Install via official builds and append binary destination directory (e.g., `C:\ffmpeg\bin`) to your System Environment variables (`PATH`).

---

## 🚀 Quick Start Setup

### 1. Initialize Virtual Workspace
Navigate to the root directory where `main.py` is located, and isolate the runtime workspace:

```bash
# Create local virtual environment
python -m venv venv

# Activate workspace (Windows Command Prompt)
venv\Scripts\activate

# Activate workspace (Mac / Linux)
source venv/bin/activate
