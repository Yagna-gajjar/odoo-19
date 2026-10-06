import json
def parse_json_response(text):
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines)
    return json.loads(text)

parse_json_response('''```json
{
    "model": "res.partner",
    "operation": "count",
    "fields": [],
    "domain": [["customer_rank", ">", 0]]
}
```''')