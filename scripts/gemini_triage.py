import sys, json, time, random, pathlib, traceback
from pydantic import BaseModel
from google import genai
from google.genai import types

issue_path = pathlib.Path(sys.argv[1])
out_json = pathlib.Path(sys.argv[2])
api_json = pathlib.Path(sys.argv[3])

class Triage(BaseModel):
    labels: list[str]
    priority: int
    rationale: str
    status: str = "ok"
    error: str | None = None

def sanitize(d: dict) -> dict:
    labels = d.get("labels") or []
    if not isinstance(labels, list):
        labels = []
    labels = [str(x).strip().lower() for x in labels if str(x).strip()]
    try:
        prio = int(d.get("priority", 3))
    except Exception:
        prio = 3
    if prio not in (1,2,3): prio = 3
    rationale = (d.get("rationale") or "").strip()
    status = d.get("status") or "ok"
    error = d.get("error")
    return Triage(labels=labels, priority=prio, rationale=rationale, status=status, error=error).model_dump()

def fallback(msg: str) -> dict:
    return Triage(labels=[], priority=3, rationale="Auto-fallback: "+msg[:500], status="error", error=msg[:1000]).model_dump()

prompt = pathlib.Path("prompts/triage.md").read_text(encoding="utf-8")
issue = issue_path.read_text(encoding="utf-8")
client = genai.Client()  # uses GEMINI_API_KEY

last_err = None
for attempt in range(1, 4):
    try:
        if attempt < 3:
            # Attempt 1-2: strict JSON via response_schema
            resp = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=f"{prompt}\n\n---\nISSUE:\n{issue}",
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=Triage,
                ),
            )
            data = json.loads(resp.text)
        else:
            # Attempt 3: plain text with strict instruction to return minified JSON
            resp = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=(f"{prompt}\n\n---\nISSUE:\n{issue}\n\n"
                          "Return ONLY a minified JSON object with keys: labels (array of strings), "
                          "priority (1-3), rationale (string). No extra text."),
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="text/plain",
                ),
            )
            data = json.loads(resp.text)

        data = sanitize(data)
        out_json.write_text(json.dumps(data, separators=(",",":")), encoding="utf-8")
        try:
            api_json.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
        except Exception:
            api_json.write_text(json.dumps({"text": resp.text}, indent=2), encoding="utf-8")
        print(str(out_json))
        break
    except Exception as e:
        last_err = e
        if attempt < 3:
            time.sleep(0.8 * attempt + random.random() * 0.4)
        else:
            tb = traceback.format_exc(limit=2)
            data = fallback(f"{type(e).__name__}: {e}")
            out_json.write_text(json.dumps(data, separators=(",",":")), encoding="utf-8")
            api_json.write_text(json.dumps({"error": str(e), "trace": tb}, indent=2), encoding="utf-8")
            print(str(out_json))
