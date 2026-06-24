# coding: utf-8
import flask
import flask_login
from flask_babel import _
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField
from wtforms.validators import InputRequired


from . import frontend
from .. import logic
from ..models import Permissions
from ..logic.object_permissions import get_user_object_permissions
from ..utils import FlaskResponseT
from ..logic import errors as logic_errors

class SampleTrackerExportForm(FlaskForm):
    proposal = StringField()
    experiment_session = StringField()


@frontend.route('/objects/<int:object_id>/export/sampletracker', methods=['POST'])
@flask_login.login_required
def sampletracker(object_id: int) -> FlaskResponseT:

    
    if Permissions.READ not in get_user_object_permissions(object_id=object_id, user_id=flask_login.current_user.id):
        return flask.abort(403)

    sampletracker_export_form = SampleTrackerExportForm()

    if sampletracker_export_form.validate_on_submit():
        try:
            logic.sampletracker.export_object(
                object_id=object_id,
                proposal=sampletracker_export_form.proposal.data,
                experiment_session=sampletracker_export_form.experiment_session.data,
            )
            flask.flash(
                _('Successfully exported object to Sample Tracker.'), 'success')
        except logic_errors.SampleTrackerNotReachableError:
            flask.flash(
                _('Sample Tracker could not be reached. Please try again later.'), 'error')
        except logic_errors.SampleTrackerExportError as e:
            flask.flash(_('Export failed (status %(code)s).',
                        code=e.status_code), 'error')
    else:
        flask.flash(
            _('Please select a proposal and an experiment session.'), 'error')

    return flask.redirect(flask.url_for('.object', object_id=object_id))