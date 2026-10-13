from odoo import fields, models


class SetuAiSchemaModel(models.Model):
    _name = 'setu.ai.schema.model'
    _description = 'AI Schema Model'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Model',
        required=True,
        index=True,
        help='Technical model name, for example res.partner.',
    )
    description = fields.Char(string='Description', required=True)
    module = fields.Char(string='Module', index=True)
    model_kind = fields.Selection(
        selection=[
            ('model', 'Persistent Model'),
            ('transient', 'Transient Model'),
            ('abstract', 'Abstract Model'),
            ('manual', 'Manual Table'),
            ('query', 'SQL View'),
        ],
        string='Kind',
        required=True,
        index=True,
        help='How this registry model is stored. Abstract models and SQL views are not normal tables.',
    )
    table_name = fields.Char(string='Table')
    is_custom = fields.Boolean(string='Custom Model')
    is_stale = fields.Boolean(string='Stale', default=False, index=True)
    last_sync = fields.Datetime(string='Last Synchronization', readonly=True)
    field_ids = fields.One2many(
        'setu.ai.schema.field',
        'schema_model_id',
        string='Fields',
    )

    _name_uniq = models.Constraint(
        'UNIQUE(name)',
        'Each technical model name can be registered only once.',
    )

    def action_synchronize_schema(self):
        """Administrator action that refreshes the schema registry."""
        return self.env['setu.ai.schema.sync'].synchronize()
