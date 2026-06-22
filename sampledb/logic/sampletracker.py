# coding: utf-8
import typing
import requests
import flask

from .objects import get_object
from . import errors

SAMPLETRACKER_TIMEOUT = 30


def export_object(
        object_id: int,
        proposal: str,
        experiment_session: str,
) -> None:
    """
    Export an object's raw data fields to the Sample Tracker endpoint.

    :param object_id: the ID of an existing object
    :param proposal: the selected proposal
    :param experiment_session: the selected experiment session
    """
    api_url = flask.current_app.config['SAMPLETRACKER_API_URL']

    object = get_object(object_id)

    payload = {
        'object_id': object_id,
        'proposal': proposal,
        'experiment_session': experiment_session,
        'data': object.data,
    }

    try:
        r = requests.post(
            url=api_url,
            json=payload,
            timeout=SAMPLETRACKER_TIMEOUT
        )
    except requests.exceptions.RequestException:
        raise errors.SampleTrackerExportError()

    if r.status_code not in {200, 201}:
        raise errors.SampleTrackerExportError()
