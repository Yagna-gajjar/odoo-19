from odoo import api, models

class OdooSchemaService(models.AbstractModel):
    _name = "setu.ai.schema"
    _description = "Odoo AI Schema Service"

    @api.model
    def get_model_catalog(self):
        catalog = {}

        for model_name, model in self.env.registry.models.items():

            if model_name.startswith("ir.") or model_name.startswith("base."):
                continue

            field_descriptions = []

            for field_name, field in model._fields.items():

                if field.string:
                    field_descriptions.append(field.string)

            catalog[model_name] = (
                    f"{model._description}. "
                    + " ".join(field_descriptions)
            )

        return catalog

    @api.model
    def get_schema(self):

        models_data = {}

        for model_name, model in self.env.registry.models.items():

            if model_name.startswith("ir.") or model_name.startswith("base."):
                continue

            fields_data = {}

            for field_name, field in model._fields.items():

                field_data = {
                    "type": field.type,
                    "string": field.string,
                }

                if field.type in (
                    "many2one",
                    "one2many",
                    "many2many",
                ):
                    field_data["relation"] = field.comodel_name

                fields_data[field_name] = field_data

            models_data[model_name] = {
                "description": model._description,
                "fields": fields_data,
            }

        return models_data

    @api.model
    def get_schema_for_models(self, model_names):
        full_schema = self.get_schema()

        return {
            model_name: full_schema[model_name]
            for model_name in model_names
            if model_name in full_schema
        }