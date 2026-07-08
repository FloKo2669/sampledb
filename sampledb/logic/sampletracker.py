import typing
import requests
import flask

from .objects import get_object
from . import errors
from .object_log import send_to_sampletracker

SAMPLETRACKER_TIMEOUT = 30


def export_object(
        object_id: int,
        version_id: int,
        user_id: int,
        proposal: str,
        experiment_session: str,
) -> None:
    """
    Export an object's raw data fields to the Sample Tracker endpoint.

    :param object_id: the ID of an existing object
    :param user_id: the ID of the user performing the export
    :param version_id: the ID of the object version to export
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
            timeout=SAMPLETRACKER_TIMEOUT,
        )
    except requests.exceptions.RequestException as e:
        raise errors.SampleTrackerNotReachableError() from e

    if r.status_code not in {200, 201}:
        raise errors.SampleTrackerExportError(r.status_code)

    send_to_sampletracker(user_id=user_id, object_id=object_id, version_id=version_id, proposal=proposal, experiment_session=experiment_session)

    try:
        return r.json().get('message', 'Export completed.')
    except ValueError:
        # response wasn't valid JSON
        return 'Export completed.'