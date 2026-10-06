import json


class OdooQueryValidator:

    ALLOWED_OPERATIONS = {
        "count",
        "search",
        "aggregate",
    }

    FORBIDDEN_KEYS = {
        "sql",
        "query",
        "create",
        "write",
        "unlink",
        "delete",
        "update",
        "drop",
        "alter",
        "truncate",
    }

    def validate(self, query, schema):

        if not isinstance(query, dict):
            raise ValueError(
                "AI response must be a JSON object."
            )


        for key in query.keys():

            if key.lower() in self.FORBIDDEN_KEYS:
                raise ValueError(
                    f"Forbidden query operation: {key}"
                )


        required_fields = {
            "model",
            "operation",
            "fields",
            "domain",
        }

        missing_fields = required_fields - query.keys()

        if missing_fields:
            raise ValueError(
                f"Missing fields: {', '.join(missing_fields)}"
            )

        model_name = query["model"]
        operation = query["operation"]
        fields = query["fields"]
        domain = query["domain"]


        if model_name not in schema:

            raise ValueError(
                f"Model '{model_name}' is not allowed."
            )

        model_schema = schema[model_name]


        if operation not in self.ALLOWED_OPERATIONS:

            raise ValueError(
                f"Operation '{operation}' is not allowed."
            )


        if not isinstance(fields, list):

            raise ValueError(
                "'fields' must be a list."
            )

        available_fields = model_schema.get(
            "fields",
            {}
        )

        for field_name in fields:

            if field_name not in available_fields:

                raise ValueError(
                    f"Field '{field_name}' does not exist "
                    f"on model '{model_name}'."
                )

        if not isinstance(domain, list):

            raise ValueError(
                "'domain' must be a list."
            )

        return True