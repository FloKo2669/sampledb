# coding: utf-8
"""
Add SEND_TO_SAMPLETRACKER enum value to ObjectLogEntryType enum.
"""

import flask_sqlalchemy

from .utils import enum_value_migration


def run(db: flask_sqlalchemy.SQLAlchemy) -> bool:
    return enum_value_migration('objectlogentrytype', 'SEND_TO_SAMPLETRACKER')
