# coding: utf-8
"""
Dynamic choice population from external sources

This module provides functionality to dynamically populate dropdown choices
in object schemas from external API sources. It allows user-specific filtering
and parameter passing while maintaining backward compatibility with static choices.
"""

import typing
import logging
import requests
from flask import current_app
from flask_babel import _

from .users import get_user
from .errors import UserDoesNotExistError

logger = logging.getLogger(__name__)

def fetch_dynamic_choices(
    source_name: str,
    user_id: int,
) -> typing.List[typing.Union[str, typing.Dict[str, str]]]:
    """
    Fetch choices from external API based on user context.

    :param source_name: The name of the configured dynamic choices source
    :param user_id: The ID of the user for filtering/authorization
    :return: List of choices
    """
    # Get configuration
    config = current_app.config.get('DYNAMIC_CHOICES_SOURCES', {})

    if source_name not in config:
        raise ValueError(f"Unknown dynamic choices source: {source_name}")

    source_config = config[source_name]

    # Get user context for API calls
    try:
        user = get_user(user_id)
    except UserDoesNotExistError:
        logger.error(
            f"User {user_id} does not exist when fetching dynamic choices")
        raise

    # Build API request
    url = source_config['url']
    headers = source_config.get('headers', {}).copy()

    # Add user context to request params
    request_params = {}
    request_params['user_id'] = user_id
    if user.email:
        request_params['user_email'] = user.email

    # Make API call
    try:
        response = requests.get(
            url,
            headers=headers,
            params=request_params,
            timeout=5
        )
        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            choices = [item['label'] if isinstance(
                item, dict) else str(item) for item in data]
        else:
            choices = []

        logger.info(
            f"Successfully fetched {len(choices)} choices from '{source_name}' for user {user_id}")
        return choices

    except requests.RequestException as e:
        logger.error(f"API call failed for source '{source_name}': {e}")
        return []
