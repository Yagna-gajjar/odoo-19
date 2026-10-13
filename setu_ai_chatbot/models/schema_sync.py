import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

_CREATE_CHUNK = 500


class SetuAiSchemaSync(models.AbstractModel):
    _name = 'setu.ai.schema.sync'
    _description = 'AI Schema Synchronization'

    @api.model
    def synchronize(self):
        """Discover models and fields from the live registry and store their metadata.

        The method reads class metadata only. It does not browse business records.
        ``sudo()`` is not used: the caller must be an administrator, and the
        schema models grant that group create and write access.
        """
        self._check_administrator()
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(hashtext('setu.ai.schema.sync'))"
        )
        now = fields.Datetime.now()
        stats = {
            'models_created': 0,
            'models_updated': 0,
            'models_unchanged': 0,
            'models_stale': 0,
            'fields_created': 0,
            'fields_updated': 0,
            'fields_unchanged': 0,
            'fields_stale': 0,
        }
        registry = self.env.registry
        schema_model_obj = self.env['setu.ai.schema.model']
        schema_field_obj = self.env['setu.ai.schema.field']
        models_by_name = {
            schema_model.name: schema_model
            for schema_model in schema_model_obj.search([])
        }
        fields_by_model = {}
        for schema_field in schema_field_obj.search([]):
            fields_by_model.setdefault(schema_field.schema_model_id.id, {})[
                schema_field.name
            ] = schema_field

        discovered = []
        create_vals = []
        for model_name, model_cls in registry.items():
            values = self._prepare_model_values(model_cls)
            schema_model = models_by_name.get(model_name)
            discovered.append((model_name, model_cls, values, schema_model))
            if not schema_model:
                create_vals.append({'name': model_name, 'last_sync': now, **values})

        if create_vals:
            for schema_model in self._create_in_chunks(schema_model_obj, create_vals):
                models_by_name[schema_model.name] = schema_model
            discovered = [
                (model_name, model_cls, values, models_by_name[model_name])
                for model_name, model_cls, values, schema_model in discovered
            ]

        field_creates = []
        seen_models = set()
        created_names = {vals['name'] for vals in create_vals}
        for model_name, model_cls, values, schema_model in discovered:
            seen_models.add(model_name)
            fields_changed = self._synchronize_fields(
                schema_model,
                model_cls,
                fields_by_model.get(schema_model.id, {}),
                field_creates,
                stats,
            )
            if model_name in created_names:
                stats['models_created'] += 1
                continue
            metadata_changed = self._values_differ(schema_model, values)
            if metadata_changed or fields_changed:
                write_vals = dict(values) if metadata_changed else {}
                write_vals['last_sync'] = now
                schema_model.write(write_vals)
                stats['models_updated'] += 1
            else:
                stats['models_unchanged'] += 1

        if field_creates:
            self._create_in_chunks(schema_field_obj, field_creates)

        for model_name, schema_model in models_by_name.items():
            if model_name in seen_models:
                continue
            self._mark_model_stale(schema_model, fields_by_model, now, stats)

        _logger.info('AI schema synchronization finished: %s', stats)
        return self._notification(stats)

    @api.model
    def _check_administrator(self):
        if self.env.su or self.env.user.has_group('base.group_system'):
            return
        raise AccessError(self.env._(
            'Only administrators can synchronize the schema registry.'
        ))

    @api.model
    def _prepare_model_values(self, model_cls):
        if model_cls._abstract:
            model_kind = 'abstract'
        elif model_cls._transient:
            model_kind = 'transient'
        elif model_cls._table_query:
            model_kind = 'query'
        elif not model_cls._auto:
            model_kind = 'manual'
        else:
            model_kind = 'model'
        return {
            'description': model_cls._description or model_cls._name,
            'module': model_cls._module or False,
            'model_kind': model_kind,
            'table_name': False if model_kind == 'abstract' else (model_cls._table or False),
            'is_custom': bool(model_cls._custom),
            'is_stale': False,
        }

    @api.model
    def _prepare_field_values(self, field):
        related = field.related or False
        if field.string:
            label = field._description_string(self.env) or field.name
        else:
            label = field.name
        help_text = False
        if field.help:
            help_text = field._description_help(self.env) or False
        return {
            'field_label': label,
            'field_type': field.type,
            'relation': field.comodel_name or False,
            'store': bool(field.store),
            'is_computed': bool(field.compute) and not related,
            'is_related': bool(related),
            'related_path': related,
            'help': help_text,
            'is_stale': False,
        }

    @api.model
    def _synchronize_fields(self, schema_model, model_cls, fields_by_name, field_creates, stats):
        changed = False
        seen = set()
        for field_name, field in model_cls._fields.items():
            seen.add(field_name)
            values = self._prepare_field_values(field)
            schema_field = fields_by_name.get(field_name)
            if not schema_field:
                field_creates.append({
                    'schema_model_id': schema_model.id,
                    'name': field_name,
                    **values,
                })
                stats['fields_created'] += 1
                changed = True
                continue
            if self._values_differ(schema_field, values):
                schema_field.write(values)
                stats['fields_updated'] += 1
                changed = True
            else:
                stats['fields_unchanged'] += 1
        for field_name, schema_field in fields_by_name.items():
            if field_name in seen:
                continue
            if schema_field.is_stale:
                stats['fields_unchanged'] += 1
                continue
            schema_field.write({'is_stale': True})
            stats['fields_stale'] += 1
            changed = True
        return changed

    @api.model
    def _mark_model_stale(self, schema_model, fields_by_model, now, stats):
        stale_fields = [
            schema_field
            for schema_field in fields_by_model.get(schema_model.id, {}).values()
            if not schema_field.is_stale
        ]
        unchanged_field_count = (
            len(fields_by_model.get(schema_model.id, {})) - len(stale_fields)
        )
        if not schema_model.is_stale:
            schema_model.write({'is_stale': True, 'last_sync': now})
            stats['models_stale'] += 1
        elif stale_fields:
            schema_model.write({'last_sync': now})
            stats['models_updated'] += 1
        else:
            stats['models_unchanged'] += 1
        if stale_fields:
            self.env['setu.ai.schema.field'].browse(
                [schema_field.id for schema_field in stale_fields]
            ).write({'is_stale': True})
            stats['fields_stale'] += len(stale_fields)
        stats['fields_unchanged'] += unchanged_field_count

    @api.model
    def _values_differ(self, record, values):
        for key, value in values.items():
            current = record[key]
            if not current and not value:
                continue
            if current != value:
                return True
        return False

    @api.model
    def _create_in_chunks(self, model, vals_list):
        records = model.browse()
        for offset in range(0, len(vals_list), _CREATE_CHUNK):
            records |= model.create(vals_list[offset:offset + _CREATE_CHUNK])
        return records

    @api.model
    def _notification(self, stats):
        message = self.env._(
            'Models: %(models_created)s created, %(models_updated)s updated, '
            '%(models_unchanged)s unchanged, %(models_stale)s marked stale. '
            'Fields: %(fields_created)s created, %(fields_updated)s updated, '
            '%(fields_unchanged)s unchanged, %(fields_stale)s marked stale.',
            **stats,
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Schema Registry'),
                'message': message,
                'type': 'success',
                'sticky': True,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }
