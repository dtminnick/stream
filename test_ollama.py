
import requests

def test_ollama_server():
    try:
        # Check available models
        resp = requests.get("http://localhost:11434/api/tags", timeout=10)
        resp.raise_for_status()
        print("✅ Ollama server is running")
        print("Available models:", resp.json())
    except Exception as e:
        print("❌ Ollama server not reachable")
        print("Error:", e)

if __name__ == "__main__":
    test_ollama_server()
