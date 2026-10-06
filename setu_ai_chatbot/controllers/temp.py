import os
from google import genai

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

chat = client.chats.create(
    model="gemini-3.6-flash"
)

response = chat.send_message(
    message="Explain Odoo ORM in one simple sentence."
)

print(response.text)