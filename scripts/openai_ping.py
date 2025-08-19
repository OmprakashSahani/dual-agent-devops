from openai import OpenAI
client = OpenAI()  # uses OPENAI_API_KEY env var
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"Say 'pong' if you can hear me."}],
)
print(resp.choices[0].message.content.strip())
