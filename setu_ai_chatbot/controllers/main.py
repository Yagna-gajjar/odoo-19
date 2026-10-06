import json
from odoo import http
from odoo.http import request

class AIAssistantController(http.Controller):

    @http.route(
        "/setu_ai_chatbot/message",
        type="jsonrpc",
        auth="user",
    )
    def send_message(self, message):

        message = (message or "").strip()

        if not message:
            return {
                "success": False,
                "reply": "Please enter a message.",
            }

        try:
            ai_service = request.env["setu.ai.service"]
            query = ai_service.generate_query(message)
            print("QUERY:", query)
            result = ai_service.execute_my_query(query)
            print("RESULT:", result)
            return {
                "success": True,
                "reply": str(result),
            }
        except ValueError as error:
            return {
                "success": False,
                "reply": str(error),
            }
        except Exception as error:
            print("AI Assistant error:", error)
            return {
                "success": False,
                "reply": "Unable to process your request.",
            }