#!/usr/bin/python
# -*- encoding: utf-8 -*-

# customize for your authorization needs

import flask
import logging
from decorator import decorator
import requests

log = logging.getLogger(__name__)


# auth implementation

def check_auth(auth):
    '''This function is called to check if a token is valid.'''
    # log.info('check_auth {} {}'.format(username, password))
    # TODO
    headers = {"Authorization": auth}
    firecloud_response = requests.get("https://api.firecloud.org/me", headers=headers)
    print(firecloud_response.json())
    return firecloud_response.status_code == 200



def authenticate():
    '''Sends a 401 response that enables basic auth'''
    return flask.Response('Please provide an API key in the Authorization header as a Bearer token', 401,
                          {'WWW-Authenticate':
                           'API key is missing or invalid'})


@decorator
def authorization_check(f, *args, **kwargs):
    '''wrap functions for authorization'''
    auth = flask.request.headers.get('Authorization', None)
    # log.debug('authorization_check auth {}'.format(auth))
    if not auth or not check_auth(auth):
        return authenticate()
    return f(*args, **kwargs)
