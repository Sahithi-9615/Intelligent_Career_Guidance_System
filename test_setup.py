import os
import sys
import subprocess
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Fix Windows encoding issue
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

def test_neo4j():
    try:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")

        if not password:
            print("❌ NEO4J_PASSWORD not set in .env file")
            return False

        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            msg = session.run("RETURN 'Neo4j Connected!' AS msg").single()["msg"]
            print(f"✅ {msg}")
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Neo4j Error: {e}")
        return False

def test_python_libs():
    try:
        import fastapi, neo4j, pandas, uvicorn
        print("✅ Python libraries imported")
        return True
    except ImportError as e:
        print(f"❌ Missing library: {e}")
        return False

def test_ollama():
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10
        )
        if result.returncode != 0:
            print("❌ Ollama not found. Install from https://ollama.ai/")
            return False

        if "llama2" not in result.stdout:
            print("❌ llama2 model not found. Run: ollama pull llama2")
            return False

        print("✅ Ollama installed with llama2 model")

        test_result = subprocess.run(
            ["ollama", "run", "llama2", "Say 'Hello' only"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=20
        )

        if test_result.returncode == 0:
            print("✅ Ollama can generate responses")
            return True
        else:
            print("⚠️ Ollama response failed")
            return True
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 Testing Setup...\n")

    results = {
        "Neo4j": test_neo4j(),
        "Python Libraries": test_python_libs(),
        "Ollama": test_ollama()
    }

    print("\n📊 RESULTS")
    for name, ok in results.items():
        print(f"{name:.<30} {'✅ PASS' if ok else '❌ FAIL'}")

    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ Fix the failed items above.\n")
