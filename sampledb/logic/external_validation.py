# coding: utf-8
"""
Logic module for validating text against externally configured validation services.

Administrators register named validators via the EXTERNAL_TEXT_VALIDATORS config
value. Object schemas reference a validator only by its configured name -- never
by URL -- so schema authors can never point this at an arbitrary address and never
see any credentials involved in reaching it.
"""
import dataclasses
import typing

import flask
import requests

from . import errors

DEFAULT_TIMEOUT_SECONDS = 10


@dataclasses.dataclass(frozen=True)
class ExternalValidationResult:
    is_valid: bool
    validated_text: typing.Optional[str]
    message: typing.Optional[str]


def run_external_validation(validator_id: str, text: str) -> ExternalValidationResult:
    """
    Send text to a configured external validator and return its verdict.

    :param validator_id: the key into the EXTERNAL_TEXT_VALIDATORS config dict
    :param text: the text to validate
    :return: the validation result
    :raise errors.ExternalValidatorNotConfiguredError: if validator_id is unknown
    :raise errors.ExternalValidatorConnectionError: if the service is unreachable
        or returns an unusable response
    """
    validators = typing.cast(
        typing.Dict[str, typing.Dict[str, typing.Any]],
        flask.current_app.config.get('EXTERNAL_VALIDATORS', {})
    )
    validator_config = validators.get(validator_id)
    if validator_config is None:
        raise errors.ExternalValidatorNotConfiguredError(f'unknown external validator: {validator_id}')

    url = validator_config['url']
    method = validator_config.get('method', 'POST')
    headers = validator_config.get('headers', {})
    timeout_seconds = validator_config.get('timeout_seconds', DEFAULT_TIMEOUT_SECONDS)
    request_field = validator_config.get('request_field', 'text')
    response_valid_field = validator_config.get('response_valid_field', 'is_valid')
    response_value_field = validator_config.get('response_value_field')
    response_message_field = validator_config.get('response_message_field')

    try:
        response = requests.request(
            method,
            url,
            json={request_field: text},
            headers=headers,
            timeout=timeout_seconds
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as exc:
        raise errors.ExternalValidatorConnectionError(f'external validator "{validator_id}" is unreachable: {exc}')
    except ValueError:
        raise errors.ExternalValidatorConnectionError(f'external validator "{validator_id}" returned invalid JSON')

    if not isinstance(result, dict):
        raise errors.ExternalValidatorConnectionError(f'external validator "{validator_id}" returned an unexpected response format')

    is_valid = bool(result.get(response_valid_field, False))
    validated_text = None
    if response_value_field and isinstance(result.get(response_value_field), str):
        validated_text = result[response_value_field]
    message = None
    if response_message_field:
        if isinstance(result.get(response_message_field), str):
            message = result[response_message_field]
    else:
        for message_field in ('message', 'error', 'detail', 'description'):
            if isinstance(result.get(message_field), str):
                message = result[message_field]
                break

    return ExternalValidationResult(is_valid=is_valid, validated_text=validated_text, message=message)