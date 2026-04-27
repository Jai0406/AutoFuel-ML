import subprocess
import sys
import time
import requests

API_URL = "http://127.0.0.1:8000"

def wait_for_backend(max_retries=30):
    """
    Blind sleep ki jagah /health poll karo with a timeout.
    Agar 30 second tak backend chalu nahi hua, toh script band kar do.
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
         "--host", "127.0.0.1", "--port", "8000",
         "--log-level", "warning"], 
    )

    # Agar backend ready ho gaya, tabhi Streamlit start karo
    if wait_for_backend():
        print("Starting Streamlit frontend...\n")
        frontend_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py"]
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
        # Agar backend fail hua toh process ko kill kar do
        backend_proc.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()