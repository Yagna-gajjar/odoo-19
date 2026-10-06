
from odoo import http
from odoo.http import request
import os
from google import genai

class AIAssistantController(http.Controller):
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    chat = client.chats.create(
        model="gemini-3.6-flash"
    )

    @http.route(
        "/setu_ai_chatbot/test_model_catalog",
        type="json",
        auth="user",
    )
    def test_model_catalog(self):
        catalog = request.env["setu.ai.schema"].get_model_catalog()

        return {
            "success": True,
            "catalog": catalog,
        }

    @http.route(
        "/setu_ai_chatbot/message",
        type="json",
        auth="user",
    )
    def send_message(self, message):
        message = (message or "").strip()

        if not message:
            return {
                "success": False,
                "reply": "Please enter a message.",
            }

        response = self.chat.send_message(
            message=message
        )

        return {
            "success": True,
            "reply": response.text
        }

    @http.route(
        "/setu_ai_chatbot/test_ai_query",
        type="json",
        auth="user",
    )
    def test_ai_query(self, question):
        schema = request.env["setu.ai.schema"].get_schema()

        result = request.env["setu.ai.service"].generate_query(
            question,
            schema,
        )

        return {
            "success": True,
            "query": result,
        }