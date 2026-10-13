import re
from datetime import date, datetime

from odoo import api, models
from odoo.exceptions import AccessError, UserError, ValidationError

_MODEL_NAME = re.compile(r'^[a-z0-9]+(?:\.[a-z0-9_]+)+$')
_FIELD_NAME = re.compile(r'^[a-z_][a-z0-9_]*$')
_ALIAS_NAME = re.compile(r'^[a-z_][a-z0-9_]{0,40}$')

_OPERATIONS = frozenset({'count', 'search', 'aggregate', 'group_aggregate'})
_QUERYABLE_KINDS = frozenset({'model', 'manual', 'query'})
_OPERATORS = frozenset({
    '=', '!=', '>', '>=', '<', '<=',
    'like', 'ilike', '=like', '=ilike', 'not like', 'not ilike',
    'in', 'not in',
    'child_of', 'parent_of',
})
_AGGREGATIONS = frozenset({'count', 'sum', 'avg', 'min', 'max'})
_NUMERIC_TYPES = frozenset({'integer', 'float', 'monetary'})
_MIN_MAX_TYPES = _NUMERIC_TYPES | frozenset({'date', 'datetime'})
_GROUPABLE_TYPES = frozenset({
    'boolean', 'char', 'selection', 'date', 'datetime',
    'integer', 'float', 'monetary', 'many2one',
})
_BLOCKED_READ_TYPES = frozenset({'binary'})
_LOGICAL = frozenset({'&', '|', '!'})
_OPERATION_KEYS = {
    'count': frozenset({'operation', 'model', 'filters', 'domain'}),
    'search': frozenset({'operation', 'model', 'fields', 'filters', 'domain', 'order', 'limit', 'offset'}),
    'aggregate': frozenset({'operation', 'model', 'aggregations', 'filters', 'domain'}),
    'group_aggregate': frozenset({
        'operation', 'model', 'groupby', 'aggregations', 'filters', 'domain', 'order', 'limit', 'offset',
    }),
}


class QueryPlanError(Exception):
    """The analytics query plan failed validation."""


class SetuAiQueryEngine(models.AbstractModel):
    _name = 'setu.ai.query.engine'
    _description = 'AI Read-Only Query Engine'

    _DEFAULT_SEARCH_LIMIT = 80
    _MAX_SEARCH_LIMIT = 200
    _MAX_GROUP_LIMIT = 100
    _MAX_OFFSET = 10000
    _MAX_FIELDS = 30
    _MAX_GROUPBY = 3
    _MAX_PATH_PARTS = 3
    _MAX_RELATION_IDS = 20

    @api.model
    def execute(self, query):
        """Validate and run a read-only analytics query.

        The schema registry decides which models and fields may be used.
        Record rules, companies, and field access come from the current user.
        ``sudo()`` is not used.
        """
        operation = query.get('operation') if isinstance(query, dict) else None
        model_name = query.get('model') if isinstance(query, dict) else None
        try:
            plan = self._validate(query)
            return self._run(plan)
        except QueryPlanError as error:
            return self._failure(operation, model_name, 'validation', str(error))
        except AccessError as error:
            return self._failure(operation, model_name, 'access', str(error))
        except (UserError, ValidationError, ValueError, KeyError):
            return self._failure(
                operation,
                model_name,
                'execution',
                'The query could not be executed.',
            )

    @api.model
    def _validate(self, query):
        if not isinstance(query, dict):
            raise QueryPlanError('The query must be a dictionary.')
        operation = query.get('operation')
        if operation not in _OPERATIONS:
            raise QueryPlanError('Unsupported operation.')
        unknown = set(query) - _OPERATION_KEYS[operation]
        if unknown:
            raise QueryPlanError('Unsupported query key: %s.' % ', '.join(sorted(unknown)))
        schema_model = self._schema_model(query.get('model'))
        live_model = self._live_model(schema_model)
        domain = self._validate_domain(schema_model, query.get('filters'), query.get('domain'))
        plan = {
            'operation': operation,
            'model': schema_model.name,
            'live_model': live_model,
            'domain': domain,
        }
        if operation == 'search':
            plan.update(self._validate_search(schema_model, live_model, query))
        elif operation == 'aggregate':
            plan['aggregations'] = self._validate_aggregations(schema_model, live_model, query.get('aggregations'))
        elif operation == 'group_aggregate':
            plan['groupby'] = self._validate_groupby(schema_model, live_model, query.get('groupby'))
            plan['aggregations'] = self._validate_aggregations(schema_model, live_model, query.get('aggregations'))
            plan['limit'] = self._validate_limit(query.get('limit'), self._MAX_GROUP_LIMIT, default=self._MAX_GROUP_LIMIT)
            plan['offset'] = self._validate_offset(query.get('offset'))
            plan['order'] = self._validate_order(
                query.get('order'),
                set(plan['groupby']) | {item['alias'] for item in plan['aggregations']},
                live_model,
                allow_aliases=True,
            )
        return plan

    @api.model
    def _schema_model(self, model_name):
        if not isinstance(model_name, str) or not _MODEL_NAME.match(model_name):
            raise QueryPlanError('The model name is invalid.')
        schema_model = self.env['setu.ai.schema.model'].search([
            ('name', '=', model_name),
        ], limit=1)
        if not schema_model:
            raise QueryPlanError('Model %s is not in the schema registry.' % model_name)
        if schema_model.is_stale:
            raise QueryPlanError('Model %s is stale. Synchronize the schema and try again.' % model_name)
        if schema_model.model_kind not in _QUERYABLE_KINDS:
            raise QueryPlanError('Model %s cannot be queried.' % model_name)
        return schema_model

    @api.model
    def _live_model(self, schema_model):
        if schema_model.name not in self.env:
            raise QueryPlanError('Model %s is not available.' % schema_model.name)
        live_model = self.env[schema_model.name]
        live_model.check_access('read')
        return live_model

    @api.model
    def _schema_field(self, schema_model, field_name):
        if not isinstance(field_name, str) or not _FIELD_NAME.match(field_name):
            raise QueryPlanError('Field name %s is invalid.' % field_name)
        schema_field = self.env['setu.ai.schema.field'].search([
            ('schema_model_id', '=', schema_model.id),
            ('name', '=', field_name),
        ], limit=1)
        if not schema_field or schema_field.is_stale:
            raise QueryPlanError('Field %s.%s is not in the schema registry.' % (schema_model.name, field_name))
        return schema_field

    @api.model
    def _live_field(self, live_model, schema_field):
        field = live_model._fields.get(schema_field.name)
        if field is None or field.type != schema_field.field_type:
            raise QueryPlanError(
                'Field %s.%s does not match the live model. Synchronize the schema and try again.'
                % (live_model._name, schema_field.name)
            )
        if not live_model._has_field_access(field, 'read'):
            raise AccessError('You cannot read %s.%s.' % (live_model._name, schema_field.name))
        return field

    @api.model
    def _validate_field_path(self, schema_model, field_path, *, for_domain=False):
        if not isinstance(field_path, str):
            raise QueryPlanError('A field path must be a string.')
        parts = field_path.split('.')
        if not parts or len(parts) > self._MAX_PATH_PARTS or any(not _FIELD_NAME.match(part) for part in parts):
            raise QueryPlanError('Field path %s is invalid.' % field_path)
        current_schema = schema_model
        current_live = self.env[schema_model.name]
        for index, part in enumerate(parts):
            schema_field = self._schema_field(current_schema, part)
            live_field = self._live_field(current_live, schema_field)
            last = index == len(parts) - 1
            if last:
                return schema_field, live_field
            if not for_domain or live_field.type not in {'many2one', 'one2many', 'many2many'} or not schema_field.relation:
                raise QueryPlanError('Field %s cannot be used in a path.' % field_path)
            current_schema = self._schema_model(schema_field.relation)
            current_live = self._live_model(current_schema)
        raise QueryPlanError('Field path %s is invalid.' % field_path)

    @api.model
    def _validate_domain(self, schema_model, filters, domain):
        combined = []
        combined.extend(self._filters_to_domain(filters))
        if domain is not None:
            if not isinstance(domain, list) or not self._domain_is_balanced(domain):
                raise QueryPlanError('The domain is invalid.')
            combined.extend(domain)
        for token in combined:
            if token in _LOGICAL:
                continue
            if not isinstance(token, (list, tuple)) or len(token) != 3:
                raise QueryPlanError('The domain is invalid.')
            field_path, operator, value = token
            if operator not in _OPERATORS:
                raise QueryPlanError('Operator %s is not supported.' % operator)
            self._validate_field_path(schema_model, field_path, for_domain=True)
            self._validate_value(operator, value)
        if not self._domain_is_balanced(combined):
            raise QueryPlanError('The domain is invalid.')
        return combined

    @api.model
    def _filters_to_domain(self, filters):
        if filters is None:
            return []
        if not isinstance(filters, list):
            raise QueryPlanError('Filters must be a list.')
        domain = []
        for item in filters:
            if not isinstance(item, dict) or set(item) - {'field', 'operator', 'value'}:
                raise QueryPlanError('Each filter needs a field, operator, and value.')
            if 'field' not in item or 'operator' not in item or 'value' not in item:
                raise QueryPlanError('Each filter needs a field, operator, and value.')
            domain.append((item['field'], item['operator'], item['value']))
        return domain

    @api.model
    def _domain_is_balanced(self, domain):
        if not domain:
            return True
        needed = 1
        for token in domain:
            if needed == 0:
                return False
            if token == '!':
                continue
            if token in {'&', '|'}:
                needed += 1
            else:
                needed -= 1
        return needed == 0

    @api.model
    def _validate_value(self, operator, value):
        if operator in {'in', 'not in'}:
            if not isinstance(value, (list, tuple)) or len(value) > 100:
                raise QueryPlanError('Operator %s needs a list of values.' % operator)
            for item in value:
                self._validate_scalar(item)
            return
        if value is None or value is False:
            if operator not in {'=', '!=', 'child_of', 'parent_of'}:
                raise QueryPlanError('This operator does not accept an empty value.')
            return
        self._validate_scalar(value)

    @api.model
    def _validate_scalar(self, value):
        if isinstance(value, bool):
            return
        if isinstance(value, int) and not isinstance(value, bool):
            return
        if isinstance(value, float):
            return
        if isinstance(value, str) and len(value) <= 500:
            return
        raise QueryPlanError('A filter value has an unsupported type.')

    @api.model
    def _validate_search(self, schema_model, live_model, query):
        field_names = query.get('fields')
        if not isinstance(field_names, list) or not field_names or len(field_names) > self._MAX_FIELDS:
            raise QueryPlanError('Search requires a list of fields.')
        if len(set(field_names)) != len(field_names):
            raise QueryPlanError('Search fields must be unique.')
        selected = []
        for field_name in field_names:
            schema_field, live_field = self._validate_field_path(schema_model, field_name)
            if '.' in field_name:
                raise QueryPlanError('Search fields must belong to the selected model.')
            if live_field.type in _BLOCKED_READ_TYPES:
                raise QueryPlanError('Field %s cannot be returned.' % field_name)
            selected.append(schema_field.name)
        return {
            'fields': selected,
            'order': self._validate_order(query.get('order'), set(selected), live_model),
            'limit': self._validate_limit(query.get('limit'), self._MAX_SEARCH_LIMIT, default=self._DEFAULT_SEARCH_LIMIT),
            'offset': self._validate_offset(query.get('offset')),
        }

    @api.model
    def _validate_order(self, order, allowed_names, live_model, allow_aliases=False):
        if order is None:
            return []
        if isinstance(order, str):
            order = self._parse_order(order)
        if not isinstance(order, list):
            raise QueryPlanError('The sort order is invalid.')
        parsed = []
        for item in order:
            if not isinstance(item, dict) or set(item) - {'field', 'direction'}:
                raise QueryPlanError('The sort order is invalid.')
            field_name = item.get('field')
            direction = (item.get('direction') or 'asc').lower()
            if direction not in {'asc', 'desc'}:
                raise QueryPlanError('Sort direction must be asc or desc.')
            if field_name not in allowed_names:
                raise QueryPlanError('Cannot sort on %s.' % field_name)
            if not allow_aliases:
                live_field = live_model._fields[field_name]
                if not live_field.store:
                    raise QueryPlanError('Cannot sort on %s.' % field_name)
            parsed.append({'field': field_name, 'direction': direction})
        return parsed

    @api.model
    def _parse_order(self, order):
        parsed = []
        for chunk in order.split(','):
            chunk = chunk.strip()
            if not chunk:
                continue
            pieces = chunk.split()
            if len(pieces) == 1:
                parsed.append({'field': pieces[0], 'direction': 'asc'})
            elif len(pieces) == 2:
                parsed.append({'field': pieces[0], 'direction': pieces[1]})
            else:
                raise QueryPlanError('The sort order is invalid.')
        return parsed

    @api.model
    def _validate_limit(self, limit, maximum, default):
        if limit is None:
            return default
        if isinstance(limit, bool) or not isinstance(limit, int) or isinstance(limit, bool):
            raise QueryPlanError('The result limit is invalid.')
        if limit < 1 or limit > maximum:
            raise QueryPlanError('The result limit must be from 1 to %s.' % maximum)
        return limit

    @api.model
    def _validate_offset(self, offset):
        if offset is None:
            return 0
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise QueryPlanError('The result offset is invalid.')
        if offset < 0 or offset > self._MAX_OFFSET:
            raise QueryPlanError('The result offset is invalid.')
        return offset

    @api.model
    def _validate_aggregations(self, schema_model, live_model, aggregations):
        if not isinstance(aggregations, list) or not aggregations:
            raise QueryPlanError('At least one aggregation is required.')
        if len(aggregations) > 10:
            raise QueryPlanError('Too many aggregations.')
        parsed = []
        aliases = set()
        for item in aggregations:
            if not isinstance(item, dict) or set(item) - {'field', 'function', 'alias'}:
                raise QueryPlanError('An aggregation is invalid.')
            function = item.get('function')
            field_name = item.get('field')
            if function not in _AGGREGATIONS:
                raise QueryPlanError('Aggregation %s is not supported.' % function)
            if function == 'count' and field_name in {'*', '__count'}:
                field_name = 'id'
            schema_field, live_field = self._validate_field_path(schema_model, field_name)
            if '.' in str(item.get('field')):
                raise QueryPlanError('Aggregations must use a field on the selected model.')
            self._check_aggregation_field(live_field, function)
            alias = item.get('alias') or '%s_%s' % (field_name, function)
            if not _ALIAS_NAME.match(alias) or alias in aliases:
                raise QueryPlanError('Aggregation alias %s is invalid.' % alias)
            aliases.add(alias)
            parsed.append({
                'field': schema_field.name,
                'function': function,
                'alias': alias,
                'spec': '%s:%s' % (schema_field.name, function),
            })
        return parsed

    @api.model
    def _check_aggregation_field(self, live_field, function):
        if function == 'count':
            return
        if not live_field.store:
            raise QueryPlanError('Field %s cannot be aggregated.' % live_field.name)
        if function in {'sum', 'avg'} and live_field.type not in _NUMERIC_TYPES:
            raise QueryPlanError('Field %s does not support %s.' % (live_field.name, function))
        if function in {'min', 'max'} and live_field.type not in _MIN_MAX_TYPES:
            raise QueryPlanError('Field %s does not support %s.' % (live_field.name, function))

    @api.model
    def _validate_groupby(self, schema_model, live_model, groupby):
        if not isinstance(groupby, list) or not groupby or len(groupby) > self._MAX_GROUPBY:
            raise QueryPlanError('Group by requires one or more fields.')
        if len(set(groupby)) != len(groupby):
            raise QueryPlanError('Group by fields must be unique.')
        validated = []
        for field_name in groupby:
            schema_field, live_field = self._validate_field_path(schema_model, field_name)
            if '.' in field_name or not live_field.store or live_field.type not in _GROUPABLE_TYPES:
                raise QueryPlanError('Cannot group by %s.' % field_name)
            validated.append(schema_field.name)
        return validated

    @api.model
    def _run(self, plan):
        operation = plan['operation']
        if operation == 'count':
            result = plan['live_model'].search_count(plan['domain'])
            return {
                'ok': True,
                'operation': operation,
                'model': plan['model'],
                'result': result,
            }
        if operation == 'search':
            return self._run_search(plan)
        if operation == 'aggregate':
            return self._run_aggregate(plan)
        return self._run_group(plan)

    @api.model
    def _run_search(self, plan):
        order = ', '.join('%s %s' % (item['field'], item['direction']) for item in plan['order'])
        records = plan['live_model'].search(
            plan['domain'],
            offset=plan['offset'],
            limit=plan['limit'],
            order=order or None,
        )
        rows = []
        for row in records.read(plan['fields']):
            rows.append(self._export_row(row))
        return {
            'ok': True,
            'operation': 'search',
            'model': plan['model'],
            'fields': plan['fields'],
            'limit': plan['limit'],
            'offset': plan['offset'],
            'record_count': len(rows),
            'records': rows,
        }

    @api.model
    def _run_aggregate(self, plan):
        specs = [item['spec'] for item in plan['aggregations']]
        grouped = plan['live_model']._read_group(plan['domain'], [], specs)
        raw_values = grouped[0] if grouped else (None,) * len(specs)
        values = {}
        for item, raw_value in zip(plan['aggregations'], raw_values):
            values[item['alias']] = self._export_scalar(raw_value)
        return {
            'ok': True,
            'operation': 'aggregate',
            'model': plan['model'],
            'values': values,
        }

    @api.model
    def _run_group(self, plan):
        specs = [item['spec'] for item in plan['aggregations']]
        fetch_limit = min(plan['limit'] + plan['offset'], self._MAX_GROUP_LIMIT)
        grouped = plan['live_model']._read_group(
            plan['domain'],
            plan['groupby'],
            specs,
            limit=fetch_limit,
        )
        groups = []
        for row in grouped:
            keys = row[:len(plan['groupby'])]
            measures = row[len(plan['groupby']):]
            groups.append({
                'key': {
                    field_name: self._export_group_key(value)
                    for field_name, value in zip(plan['groupby'], keys)
                },
                'values': {
                    item['alias']: self._export_scalar(value)
                    for item, value in zip(plan['aggregations'], measures)
                },
            })
        groups = self._sort_groups(groups, plan['order'])
        sliced = groups[plan['offset']:plan['offset'] + plan['limit']]
        return {
            'ok': True,
            'operation': 'group_aggregate',
            'model': plan['model'],
            'groupby': plan['groupby'],
            'limit': plan['limit'],
            'offset': plan['offset'],
            'truncated': len(grouped) >= fetch_limit and plan['offset'] + plan['limit'] >= fetch_limit,
            'group_count': len(sliced),
            'groups': sliced,
        }

    @api.model
    def _sort_groups(self, groups, order):
        if not order:
            return groups
        for item in reversed(order):
            reverse = item['direction'] == 'desc'
            field_name = item['field']

            def sort_key(group, name=field_name):
                if name in group['key']:
                    return (group['key'][name] is None, self._sort_token(group['key'][name]))
                return (group['values'].get(name) is None, self._sort_token(group['values'].get(name)))

            groups.sort(key=sort_key, reverse=reverse)
        return groups

    @api.model
    def _sort_token(self, value):
        if isinstance(value, dict):
            return value.get('id') or 0
        if isinstance(value, (int, float, str)):
            return value
        return str(value)

    @api.model
    def _export_row(self, row):
        exported = {}
        for key, value in row.items():
            exported[key] = self._export_scalar(value)
        return exported

    @api.model
    def _export_scalar(self, value):
        if isinstance(value, bool) or value is None:
            return value
        if value is False:
            return None
        if isinstance(value, datetime):
            return value.isoformat(sep=' ')
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, tuple):
            if len(value) == 2 and isinstance(value[0], int):
                return {'id': value[0], 'name': value[1]}
            return [self._export_scalar(item) for item in value]
        if isinstance(value, list):
            exported = [self._export_scalar(item) for item in value[:self._MAX_RELATION_IDS]]
            return exported
        if isinstance(value, models.BaseModel):
            return self._export_recordset(value)
        if isinstance(value, (int, float, str)):
            return value
        raise QueryPlanError('The query returned a value that cannot be serialized.')

    @api.model
    def _export_group_key(self, value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, models.BaseModel):
            return self._export_recordset(value)
        return self._export_scalar(value)

    @api.model
    def _export_recordset(self, records):
        if not records:
            return None
        if len(records) == 1:
            return {'id': records.id, 'name': records.display_name}
        return [
            {'id': record.id, 'name': record.display_name}
            for record in records[:self._MAX_RELATION_IDS]
        ]

    @api.model
    def _failure(self, operation, model_name, error_type, message):
        return {
            'ok': False,
            'operation': operation,
            'model': model_name,
            'error': {
                'type': error_type,
                'message': message,
            },
        }
