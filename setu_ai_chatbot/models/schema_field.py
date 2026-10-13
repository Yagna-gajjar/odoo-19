from odoo import fields, models


class SetuAiSchemaField(models.Model):
    _name = 'setu.ai.schema.field'
    _description = 'AI Schema Field'
    _order = 'schema_model_id, name'
    _rec_name = 'name'

    schema_model_id = fields.Many2one(
        'setu.ai.schema.model',
        string='Model',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Field', required=True, index=True)
    field_label = fields.Char(string='Label', required=True)
    field_type = fields.Char(string='Type', required=True)
    relation = fields.Char(string='Related Model')
    store = fields.Boolean(string='Stored')
    is_computed = fields.Boolean(string='Computed')
    is_related = fields.Boolean(string='Related')
    related_path = fields.Char(string='Related Path')
    help = fields.Text(string='Help')
    is_stale = fields.Boolean(string='Stale', default=False, index=True)

    _model_field_uniq = models.Constraint(
        'UNIQUE(schema_model_id, name)',
        'Each field name can be registered only once per model.',
    )
