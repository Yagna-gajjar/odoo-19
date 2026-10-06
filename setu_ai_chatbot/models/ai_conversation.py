from odoo import models, fields


class AIConversation(models.Model):
    _name = "ai.conversation"
    _description = "AI Conversation"

    name = fields.Char(
        string="Conversation",
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.user,
        required=True,
    )

    message_ids = fields.One2many(
        "ai.message",
        "conversation_id",
        string="Messages",
    )

    active = fields.Boolean(
        default=True,
    )