import subprocess
import threading
import time
import webview
import requests

def run_streamlit():
    subprocess.Popen(
        ["streamlit", "run", "streamlit_app.py"],
        cwd="app" 
    )

def wait_until_ready(url, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"Server at {url} not responding.")

if __name__ == "__main__":
    threading.Thread(target=run_streamlit).start()
    wait_until_ready("http://localhost:8501")
    webview.create_window("Streamlit App", "http://localhost:8501", width=1200, height=800)
    webview.start()
