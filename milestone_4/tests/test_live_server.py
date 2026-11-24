"""
Verifies that the live Milestone 4 Uvicorn server starts and responds to HTTP requests.
"""
import subprocess
import time
import sys
import urllib.request
import json

def test_live():
    print("Starting Milestone 4 server in subprocess...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8899"],
        cwd="C:/Trakerz/milestone_4/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        time.sleep(2.5)

        url = "http://127.0.0.1:8899/api/health"
        print(f"Probing {url}...")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            data = json.loads(body)
            print(f"Response status: {status_code}")
            print(f"Response body: {data}")
            assert status_code == 200
            assert data.get("status") == "healthy"
            print("Milestone 4 Live server test SUCCESSFUL!")
    finally:
        print("Terminating server process...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Server process stopped.")

if __name__ == "__main__":
    test_live()
