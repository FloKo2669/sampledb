# coding: utf-8
"""
Proxy endpoint for external_validator field type.

When a user fills in an external_validator field and clicks the Validate button,
the browser POSTs to this endpoint. The endpoint looks up the configured validator
URL from the action schema (the URL never travels through the browser), then
forwards the text to the external service and returns a normalised response.
"""
import typing

import flask
import flask_login
import requests as http_client

from ... import logic
from ...utils import FlaskResponseT
from .forms import ObjectForm
from .. import frontend


def _navigate_schema(
        root_schema: typing.Dict[str, typing.Any],
        id_prefix: str
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    """
    Navigate an action schema using the id_prefix string to find the sub-schema.

    id_prefix follows the pattern  ``{root}__{key1}__{key2}..._``  where
    numeric keys denote array item indices.

    :param root_schema: the root action schema dict
    :param id_prefix:   the field id_prefix from the form (e.g. ``object__formula_``)
    :return: the sub-schema dict, or None if the path cannot be resolved
    """
    parts = id_prefix.rstrip('_').split('__')
    # parts[0] is the id_prefix_root ('object') – skip it
    schema = root_schema
    try:
        for part in parts[1:]:
            if schema['type'] == 'object':
                schema = schema['properties'][part]
            elif schema['type'] == 'array':
                # numeric index → navigate into items schema
                int(part)   # validate that it is a number
                schema = schema['items']
            else:
                return None
    except (KeyError, ValueError, TypeError):
        return None
    return schema


@frontend.route('/objects/external_validator_proxy', methods=['POST'])
@flask_login.login_required
def external_validator_proxy() -> FlaskResponseT:
    """
    Server-side proxy for external_validator field validation.

    Accepts a multipart/form-data POST with:
    - csrf_token   : the WTF CSRF token (validated automatically)
    - action_id    : integer ID of the action whose schema contains the field
    - id_prefix    : id_prefix of the field (e.g. ``object__formula_``)
    - text         : the text to send to the external validator

    Returns JSON:
    - valid          : bool
    - validated_text : string | null
    - message        : string (optional error/info message from the external service)
    """
    # CSRF validation via an empty FlaskForm
    form = ObjectForm()
    if not form.validate():
        return flask.jsonify({'error': 'Invalid CSRF token'}), 400

    action_id_str = flask.request.form.get('action_id', '').strip()
    id_prefix = flask.request.form.get('id_prefix', '').strip()
    text = flask.request.form.get('text', '')

    if not action_id_str:
        return flask.jsonify({'error': 'Missing action_id'}), 400
    try:
        action_id = int(action_id_str)
    except ValueError:
        return flask.jsonify({'error': 'Invalid action_id'}), 400

    try:
        action = logic.actions.get_action(action_id)
    except logic.errors.ActionDoesNotExistError:
        return flask.jsonify({'error': 'Action not found'}), 404

    if action.schema is None:
        return flask.jsonify({'error': 'Action has no schema'}), 400

    field_schema = _navigate_schema(action.schema, id_prefix)
    if field_schema is None:
        return flask.jsonify({'error': 'Field not found in schema'}), 400
    if field_schema.get('type') != 'external_validator':
        return flask.jsonify({'error': 'Field is not an external_validator'}), 400

    validator_url: str = field_schema['url']
    request_field: str = field_schema.get('request_field', 'formula')
    response_valid_field: str = field_schema.get('response_valid_field', 'is_valid')
    response_value_field: typing.Optional[str] = field_schema.get('response_value_field', 'result')

    try:
        response = http_client.post(
            validator_url,
            json={request_field: text},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        print(result)
    except http_client.exceptions.Timeout:
        return flask.jsonify({'error': 'External validator timed out'}), 502
    except http_client.exceptions.RequestException as exc:
        return flask.jsonify({'error': f'External validator error: {exc}'}), 502
    except ValueError:
        return flask.jsonify({'error': 'External validator returned invalid JSON'}), 502

    valid = bool(result.get(response_valid_field, False))
    validated_text: typing.Optional[str] = None
    if response_value_field and response_value_field in result:
        validated_text = str(result[response_value_field])

    message: typing.Optional[str] = None
    for msg_key in ('message', 'error', 'detail', 'description'):
        if msg_key in result and isinstance(result[msg_key], str):
            message = result[msg_key]
            break

    return flask.jsonify({
        'valid': valid,
        'validated_text': validated_text,
        'message': message,
    })
