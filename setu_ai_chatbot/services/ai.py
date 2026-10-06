import json
from odoo import api, models
from .model_retriever import OdooModelRetriever
from .client import client
from ...temp import parse_json_response

retriever = OdooModelRetriever()


class OdooAIService(models.AbstractModel):
    _name = "setu.ai.service"
    _description = "Odoo AI Service"

    def parse_json_response(self, text):
        text = text.strip()

        if text.startswith("```"):
            lines = text.splitlines()

            if lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines)
        return json.loads(text)


    @api.model
    def execute_my_query(self, query):

        new_query = parse_json_response(query)

        model_name = new_query["model"]
        operation = new_query["operation"]

        fields = new_query.get("fields", [])
        domain = new_query.get("domain", [])
        limit = new_query.get("limit")
        offset = new_query.get("offset")
        sort = new_query.get("sort")
        group_by = new_query.get("group_by", [])
        aggregates = new_query.get("aggregates", [])

        domain = [
            tuple(condition)
            if isinstance(condition, list)
            else condition
            for condition in domain
        ]

        model = self.env[model_name]

        # COUNT
        if operation == "count":

            return model.search_count(domain)

        # SEARCH
        elif operation == "search":

            records = model.search(
                domain,
                offset=offset or 0,
                limit=limit,
                order=sort,
            )

            result = []

            for record in records:

                row = {}

                for field in fields:
                    row[field] = record[field]

                result.append(row)

            return result

        # AGGREGATE
        elif operation == "aggregate":

            result = model.read_group(
                domain=domain,
                fields=aggregates,
                groupby=group_by,
                offset=offset or 0,
                limit=limit,
                order=sort,
            )

            return result

        # INVALID
        else:
            raise ValueError(
                f"Unsupported operation: {operation}"
            )

    @api.model
    def generate_query(self, question):
        schema_service = self.env["setu.ai.schema"]
        catalog = schema_service.get_model_catalog()

        relevant_models = retriever.find_relevant_models(
            question,
            catalog,
            top_k=5,
        )
        model_names = [
            item["model"]
            for item in relevant_models
        ]

        relevant_schema = schema_service.get_schema_for_models(
            model_names
        )
        print("QUESTION:", question)

        print("RELEVANT MODELS:")
        for model in relevant_models:
            print(model)

        prompt = f"""
            You are an AI data analyst working with Odoo.

            The user asked:

            {question}

            Here is the Odoo database schema:

            {json.dumps(relevant_schema, indent=2)}

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
