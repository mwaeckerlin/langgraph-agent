"""E2E tests for mwaeckerlin/langgraph-agent, run inside the compose network.

Phase `before` runs the API checks and writes a thread to the database; the
runner then restarts the agent, and phase `after` reads that thread again.
Only the Python standard library is used.
"""
import json
import sys
import time
import urllib.error
import urllib.request

PHASE = sys.argv[1] if len(sys.argv) > 1 else "before"
THREAD_FILE = "/state/thread-id"
results = []


def check(name, condition, detail=""):
    results.append(condition)
    print(f"  {'PASS' if condition else 'FAIL'}  {name}" + ("" if condition else f": {detail}"))


def call(method, url, body=None, key=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if key:
        request.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def wait_for(url):
    for _ in range(120):
        try:
            if call("GET", url + "/ok")[0] == 200:
                return
        except OSError:
            pass
        time.sleep(1)
    raise SystemExit(f"{url} did not answer")


AGENT, SECRET, OPEN, LLM = "http://agent:8000", "http://agent-secret:8000", "http://agent-open:8000", "http://agent-llm:8000"
for url in (AGENT, SECRET, OPEN, LLM):
    wait_for(url)

if PHASE == "before":
    print("==> E2E: API")
    status, body = call("GET", AGENT + "/ok")
    check("health_without_token", status == 200 and body == {"status": "ok"}, (status, body))

    check("graphs_refused_without_token", call("GET", AGENT + "/graphs")[0] == 401)
    check("graphs_refused_with_wrong_token", call("GET", AGENT + "/graphs", key="wrong")[0] == 401)
    status, body = call("GET", AGENT + "/graphs", key="env-key")
    names = sorted(g["name"] for g in body) if status == 200 else body
    check("graphs_listed_with_token", names == ["echo", "upper"], (status, body))

    status, body = call("POST", AGENT + "/runs", {"graph_name": "echo", "input": {"message": "hello"}, "config": {}}, key="env-key")
    check("stateless_run_echo", status == 200 and body["output"]["response"] == "[local-echo] hello", (status, body))
    status, body = call("POST", AGENT + "/runs", {"graph_name": "upper", "input": {"message": "hello"}, "config": {}}, key="env-key")
    check("graph_from_graphs_dir_runs", status == 200 and body["output"]["response"] == "HELLO", (status, body))
    check("unknown_graph_404", call("POST", AGENT + "/runs", {"graph_name": "nope", "input": {}, "config": {}}, key="env-key")[0] == 404)
    check("run_refused_without_token", call("POST", AGENT + "/runs", {"graph_name": "echo", "input": {"message": "x"}, "config": {}})[0] == 401)

    status, body = call("POST", AGENT + "/threads", key="env-key")
    thread = body["thread_id"] if status == 200 else ""
    check("thread_created", status == 200 and len(thread) == 36, (status, body))
    status, body = call("POST", f"{AGENT}/threads/{thread}/runs", {"graph_name": "echo", "input": {"message": "remember me"}, "config": {}}, key="env-key")
    check("thread_run", status == 200 and body["output"]["response"] == "[local-echo] remember me", (status, body))
    status, body = call("GET", f"{AGENT}/threads/{thread}/state", key="env-key")
    check("thread_state_stored", status == 200 and body.get("message") == "remember me", (status, body))
    check("unknown_thread_404", call("GET", f"{AGENT}/threads/00000000-0000-0000-0000-000000000000/state", key="env-key")[0] == 404)
    open(THREAD_FILE, "w").write(thread)

    check("secret_key_accepted", call("GET", SECRET + "/graphs", key="secret-key")[0] == 200)
    check("secret_wins_over_environment", call("GET", SECRET + "/graphs", key="env-key-that-must-lose")[0] == 401)
    status, body = call("POST", SECRET + "/threads", key="secret-key")
    status, body = call("POST", f"{SECRET}/threads/{body['thread_id']}/runs", {"graph_name": "echo", "input": {"message": "db from secret"}, "config": {}}, key="secret-key")
    check("database_from_password_secret", status == 200, (status, body))

    check("no_key_means_no_authentication", call("GET", OPEN + "/graphs")[0] == 200)

    status, body = call("POST", LLM + "/runs", {"graph_name": "echo", "input": {"message": "ask the model"}, "config": {}})
    answer = body["output"]["response"] if status == 200 else body
    check("llm_answers_with_configured_model", answer == "model=e2e-model key=Bearer e2e-llm-key said=ask the model", answer)
else:
    print("==> E2E: after restart")
    thread = open(THREAD_FILE).read()
    status, body = call("GET", f"{AGENT}/threads/{thread}/state", key="env-key")
    check("thread_state_survives_restart", status == 200 and body.get("message") == "remember me", (status, body))

print(f"\n==> E2E results ({PHASE}): {results.count(True)} passed, {results.count(False)} failed")
sys.exit(0 if all(results) else 1)
