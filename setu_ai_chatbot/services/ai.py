import json
import os

from google import genai
from odoo import api, models

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

class OdooAIService(models.AbstractModel):
    _name = "setu.ai.service"
    _description = "Odoo AI Service"

    @api.model
    def generate_query(self, question, schema):

        prompt = f"""
            You are an AI data analyst working with Odoo.
            
            The user asked:
            
            {question}
            
            Here is the Odoo database schema:
            
            {json.dumps(schema, indent=2)}
            
            Your job is to determine what Odoo data is required to answer
            the user's question.
            
            Return ONLY valid JSON.
            
            The JSON must have this structure:
            
            {{
                "model": "technical.model.name",
                "operation": "count | search | aggregate",
                "fields": [],
                "domain": []
            }}
            
            Do not write SQL.
            Do not execute anything.
            Do not explain your answer.
            """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text