"""
Verifies that the live Milestone 5 Uvicorn server starts and responds to HTTP requests.
"""
import subprocess
import time
import sys
import urllib.request
import json

def test_live():
    print("Starting Milestone 5 server in subprocess...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8905"],
        cwd="C:/Trakerz/milestone_5/backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        time.sleep(2.5)

        for path in ["/api/health", "/api/ai/status", "/"]:
            url = f"http://127.0.0.1:8905{path}"
            print(f"Probing {url}...")
            with urllib.request.urlopen(urllib.request.Request(url), timeout=5) as response:
                status_code = response.getcode()
                body = response.read().decode("utf-8")
                assert status_code == 200
                if path.startswith("/api/"):
                    data = json.loads(body)
                    print(f"  {path} -> 200 OK: {data}")
                else:
                    assert "AI Suite M5" in body
                    assert "view-assistant" in body
                    print(f"  {path} -> 200 OK (HTML length: {len(body)} chars)")
        print("Milestone 5 Live server verification SUCCESSFUL!")
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
