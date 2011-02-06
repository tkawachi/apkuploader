"""
Manages the namespace for the application.

Has a separate namespace for each Google Apps.
"""

__author__ = 'kawachi@tonchidot.com'

from google.appengine.api import namespace_manager

def namespace_manager_default_namespace_for_request():
    return namespace_manager.google_apps_namespace()
