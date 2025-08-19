import sys, json, pathlib
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

prompt = pathlib.Path("prompts/triage.md").read_text(encoding="utf-8")
issue = issue_path.read_text(encoding="utf-8")

client = genai.Client()  # reads GEMINI_API_KEY from env

resp = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=f"{prompt}\n\n---\nISSUE:\n{issue}",
    config=types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=Triage,  # enforce strict JSON schema
    ),
)

# Write the assistant JSON (minified)
data = json.loads(resp.text)
out_json.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")

# Try to persist the full API response (best-effort)
try:
    api_json.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
except Exception:
    api_json.write_text(json.dumps({"text": resp.text}, indent=2), encoding="utf-8")

print(str(out_json))
