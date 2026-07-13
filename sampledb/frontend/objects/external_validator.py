"""
Proxy endpoint for external_validator field type.

When a user fills in an external_validator field and clicks the Validate button,
the browser POSTs the configured validator name and text to this endpoint. This
gives instant feedback while editing. It is NOT the authoritative check: the same
external service is called again, server-side, when the object is actually saved
(see logic/schemas/validate.py's _validate_external_validator), so this endpoint
being skipped or its result being tampered with client-side cannot bypass that.
"""
import flask
import flask_login

from ...utils import FlaskResponseT
from ...logic import errors, external_validation
from .forms import ObjectForm
from .. import frontend


@frontend.route('/objects/external_validator_proxy', methods=['POST'])
@flask_login.login_required
def external_validator_proxy() -> FlaskResponseT:
    """
    Server-side proxy for external_validator field validation.

    Accepts a multipart/form-data POST with:
    - validator    : the configured validator name
    - text         : the text to send to the external validator

    Returns JSON:
    - valid          : bool
    - validated_text : string | null
    - message        : string (optional error/info message from the external service)
    """
    form = ObjectForm()
    if not form.validate():
        return flask.jsonify({'error': 'Invalid CSRF token'}), 400

    validator_name = flask.request.form.get('validator', '').strip()
    text = flask.request.form.get('text', '')

    if not validator_name:
        return flask.jsonify({'error': 'Missing validator'}), 400

    try:
        result = external_validation.run_external_validation(validator_name, text)
    except errors.ExternalValidatorNotConfiguredError:
        return flask.jsonify({'error': 'Unknown external validator'}), 400
    except errors.ExternalValidatorConnectionError as exc:
        return flask.jsonify({'error': str(exc)}), 502

    return flask.jsonify({
        'valid': result.is_valid,
        'validated_text': result.validated_text,
        'message': result.message,
    })