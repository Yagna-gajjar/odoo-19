from odoo import models, fields


class AIMessage(models.Model):
    _name = "ai.message"
    _description = "AI Message"

    conversation_id = fields.Many2one(
        "ai.conversation",
        string="Conversation",
        required=True,
        ondelete="cascade",
    )

    role = fields.Selection(
        [
            ("user", "User"),
            ("assistant", "Assistant"),
        ],
        string="Role",
        required=True,
    )

    content = fields.Text(
        string="Message",
        required=True,
    )

    create_date = fields.Datetime(
        string="Created On",
        readonly=True,
    )