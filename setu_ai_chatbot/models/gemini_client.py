import json
import logging
import os
import re
import time
import urllib.error
import urllib.request

from odoo import api, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

_MODEL_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$')
_API_KEY_PARAMETER = 'setu_ai_chatbot.gemini_api_key'
_MODEL_PARAMETER = 'setu_ai_chatbot.gemini_model'
_DEFAULT_MODEL = 'gemini-2.5-flash'
_PLACEHOLDER_KEYS = frozenset({'your-key', 'your_key', 'changeme', 'api-key', 'todo'})
_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'
_TIMEOUT = 30
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_RETRY_DELAYS = (1, 2)


class GeminiError(Exception):
    """Base error for the Gemini client."""

    error_type = 'api'


class GeminiConfigurationError(GeminiError):
    error_type = 'configuration'


class GeminiRateLimitError(GeminiError):
    error_type = 'rate_limit'


class GeminiResponseError(GeminiError):
    error_type = 'malformed'


class SetuAiGeminiClient(models.AbstractModel):
    _name = 'setu.ai.gemini.client'
    _description = 'Gemini API Client'

    @api.model
    def generate(self, prompt, response_schema):
        """Send one prompt and return the parsed JSON object.

        ``GEMINI_API_KEY`` is used when it is set. Otherwise the key is read from
        the system parameter ``setu_ai_chatbot.gemini_api_key``. The key is sent
        as a header and is not written to the log.
        """
        api_key = self._api_key()
        if not api_key:
            raise GeminiConfigurationError('Gemini API key is not configured.')
        model_name = self._model_name()
        payload = {
            'contents': [{
                'role': 'user',
                'parts': [{'text': prompt}],
            }],
            'generationConfig': {
                'temperature': 0,
                'responseMimeType': 'application/json',
                'responseSchema': response_schema,
            },
        }
        body = json.dumps(payload).encode()
        attempts = len(_RETRY_DELAYS) + 1
        for attempt in range(attempts):
            request = urllib.request.Request(
                _ENDPOINT % model_name,
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': api_key,
                },
                method='POST',
            )
            try:
                with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
                    raw = response.read().decode('utf-8')
                return self._parse_response(raw)
            except urllib.error.HTTPError as error:
                if error.code in _RETRY_STATUSES and attempt < attempts - 1:
                    _logger.warning('Gemini request failed with status %s. Retrying.', error.code)
                    time.sleep(_RETRY_DELAYS[attempt])
                    continue
                if error.code == 429:
                    _logger.warning('Gemini request failed with status 429.')
                    raise GeminiRateLimitError('Gemini rate limit was reached. Try again later.') from error
                message = self._http_error_message(error, api_key)
                _logger.warning(message)
                raise GeminiError(message) from error
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                message = self._network_error_message(error, api_key)
                _logger.warning(message)
                raise GeminiError(message) from error

    @api.model
    def _api_key(self):
        env_key = (os.environ.get('GEMINI_API_KEY') or '').strip()
        if env_key and env_key.lower() not in _PLACEHOLDER_KEYS:
            return env_key
        configured = ''
        try:
            configured = self.env['ir.config_parameter'].get_param(_API_KEY_PARAMETER) or ''
        except AccessError:
            configured = ''
        if isinstance(configured, str):
            configured = configured.strip()
            if configured and configured.lower() not in _PLACEHOLDER_KEYS:
                return configured
        return ''

    @api.model
    def _http_error_message(self, error, api_key):
        detail = ''
        try:
            payload = json.loads(error.read().decode('utf-8', errors='replace'))
            detail = ((payload.get('error') or {}).get('message')) or ''
        except (json.JSONDecodeError, OSError, UnicodeError, AttributeError):
            detail = ''
        if api_key and detail:
            detail = detail.replace(api_key, '[redacted]')
        if detail:
            return 'Gemini request failed (%s): %s' % (error.code, detail[:300])
        return 'Gemini request failed (%s).' % error.code

    @api.model
    def _network_error_message(self, error, api_key):
        reason = getattr(error, 'reason', '') or ''
        detail = str(reason).replace('\n', ' ').replace('\r', ' ').strip()
        if api_key and detail:
            detail = detail.replace(api_key, '[redacted]')
        if detail:
            return 'Gemini request failed: %s' % detail[:300]
        return 'Gemini request failed.'

    @api.model
    def _model_name(self):
        configured = self.env['ir.config_parameter'].get_param(_MODEL_PARAMETER, default=_DEFAULT_MODEL)
        model_name = (configured or _DEFAULT_MODEL).strip()
        if not _MODEL_NAME.match(model_name):
            return _DEFAULT_MODEL
        return model_name

    @api.model
    def _parse_response(self, raw):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise GeminiResponseError('Gemini returned malformed JSON.') from error
        candidates = payload.get('candidates') or []
        if not candidates:
            raise GeminiResponseError('Gemini returned no content.')
        parts = ((candidates[0].get('content') or {}).get('parts')) or []
        text = ''
        for part in parts:
            if isinstance(part, dict) and part.get('text'):
                text = part['text']
                break
        return self._parse_json_object(text)

    @api.model
    def _parse_json_object(self, text):
        if isinstance(text, dict):
            return text
        if not isinstance(text, str) or not text.strip():
            raise GeminiResponseError('Gemini returned malformed JSON.')
        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise GeminiResponseError('Gemini returned malformed JSON.') from error
        if not isinstance(value, dict):
            raise GeminiResponseError('Gemini returned malformed JSON.')
        return value
