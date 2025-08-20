import sys, json, pathlib, traceback
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

issue_path = pathlib.Path(sys.argv[1])
out_json = pathlib.Path(sys.argv[2])
api_json = pathlib.Path(sys.argv[3])

class Triage(BaseModel):
    labels: list[str]
    priority: int
    rationale: str
    status: str = "ok"   # new: "ok" | "error"
    error: str | None = None

def _fallback(msg: str) -> dict:
    return Triage(labels=[], priority=3,
                  rationale="Auto-fallback: "+msg[:500],
                  status="error", error=msg[:1000]).model_dump()

def _sanitize(d: dict) -> dict:
    # ensure required fields exist and look sane
    labels = d.get("labels") or []
    if not isinstance(labels, list):
        labels = []
    labels = [str(x).strip().lower() for x in labels if str(x).strip()]
    prio = d.get("priority")
    try:
        prio = int(prio)
    except Exception:
        prio = 3
    if prio not in (1,2,3):
        prio = 3
    rationale = (d.get("rationale") or "").strip()
    status = d.get("status") or "ok"
    error = d.get("error")
    return Triage(labels=labels, priority=prio, rationale=rationale, status=status, error=error).model_dump()

prompt = pathlib.Path("prompts/triage.md").read_text(encoding="utf-8")
issue = issue_path.read_text(encoding="utf-8")

client = genai.Client()  # reads GEMINI_API_KEY

try:
    resp = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"{prompt}\n\n---\nISSUE:\n{issue}",
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=Triage,
        ),
    )
    # Primary path: strict JSON from the SDK
    data = json.loads(resp.text)
    data = _sanitize(data)
    # Write assistant JSON (minified)
    out_json.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    # Save API response best-effort
    try:
        api_json.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
    except Exception:
        api_json.write_text(json.dumps({"text": resp.text}, indent=2), encoding="utf-8")
    print(str(out_json))
except Exception as e:
    # Fallback path: always write something structured
    tb = traceback.format_exc(limit=2)
    data = _fallback(f"{type(e).__name__}: {e}")
    out_json.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    api_json.write_text(json.dumps({"error": str(e), "trace": tb}, indent=2), encoding="utf-8")
    print(str(out_json))
