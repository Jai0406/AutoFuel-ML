import subprocess
import sys
import time
import requests

API_URL = "http://127.0.0.1:8000"

def wait_for_backend(max_retries=30):
    """
    Actively polls the FastAPI '/health' endpoint to verify server readiness.

    Replaces unreliable static sleep delays with a dynamic polling mechanism. 
    This ensures that dependent services (e.g., the Streamlit frontend) only 
    initialize after the backend ML models and API routes are fully loaded 
    and operational.

    Args:
        max_retries (int, optional): Maximum number of polling attempts 
                                     (1 attempt per second). Defaults to 30.

    Returns:
        bool: True if the backend responds with HTTP 200 within the retry limit, 
              False if the connection times out and maximum retries are exhausted.
    """
    print("   Waiting for backend to be ready...", end="", flush=True)
    retries = 0
    while retries < max_retries:
        try:
            if requests.get(f"{API_URL}/health", timeout=1).status_code == 200:
                print(" Ready. ✅")
                return True
        except requests.exceptions.ConnectionError:
            print(".", end="", flush=True)
            time.sleep(1)
            retries += 1 
            
    print("\n❌ Error: Backend failed to start after 30 seconds. Check api.py for errors.")
    return False

def main():
    print("\n🚀 Starting FastAPI backend on port 8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app",
         "--host", "0.0.0.0", "--port", "8000",
         "--log-level", "warning"], 
    )

    # Agar backend ready ho gaya, tabhi Streamlit start karo
    if wait_for_backend():
        print("Starting Streamlit frontend...\n")
        frontend_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
        )

        try:
            frontend_proc.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down servers...")
            frontend_proc.terminate()
            backend_proc.terminate()
            frontend_proc.wait()
            backend_proc.wait()
            print("✅ Done.")
    else:
        backend_proc.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()