#!/usr/bin/env python

import httplib
try:
    import simplejson as json
except ImportError:
    import json
import os
import sys
import traceback
from urlparse import urljoin
import argparse
try:
    import requests
except ImportError:
    raise ImportError('Missing dependency requests. \
                      Do ``pip install requests``.')

try:
    import yaml
    requests.packages.urllib3.disable_warnings()
except ImportError:
    raise ImportError('Missing dependency pyyaml. \
                      Do ``pip install pyyaml``.')

# dev-github configuration

dev-github_API_BASE_URL = None
dev-github_AUTH_BASE_URL = None
dev-github_USERNAME = None
dev-github_PASSWORD = None
dev-github_API_KEY = None
dev-github_AUTH_TOKEN = None
dev-github_SSL_VERIFY = False

dev-github_AUTH_PATH = 'tokens'
dev-github_WEBHOOKS_PATH = 'webhooks/dev-github'
dev-github_TRIGGERS_PATH = 'triggertypes'
dev-github_TRIGGERTYPE_PACK = 'nagios'
dev-github_TRIGGERTYPE_NAME = 'service_state_change'
dev-github_TRIGGERTYPE_REF = '.'.join([dev-github_TRIGGERTYPE_PACK, dev-github_TRIGGERTYPE_NAME])

STATE_MESSAGE = {
    'OK': 'All is well on the Western front.',
    'WARNING': 'We gots a warning yo!',
    'UNKNOWN': 'It be unknown...',
    'CRITICAL': 'Critical!'
}

REGISTERED_WITH_dev-github = False
UNAUTHED = False
IS_API_KEY_AUTH = False

OK_CODES = [httplib.OK, httplib.CREATED, httplib.ACCEPTED, httplib.CONFLICT]
UNREACHABLE_CODES = [httplib.NOT_FOUND]

TOKEN_AUTH_HEADER = 'X-Auth-Token'
API_KEY_AUTH_HEADER = 'dev-github-Api-Key'


def _create_trigger_type(verbose=False):
    try:
        url = _get_dev-github_triggers_base_url()
        payload = {
            'name': dev-github_TRIGGERTYPE_NAME,
            'pack': dev-github_TRIGGERTYPE_PACK,
            'description': 'Trigger type for nagios event handler.'
        }

        headers = _get_dev-github_request_headers()
        headers['Content-Type'] = 'application/json; charset=utf-8'

        if verbose:
            print('POST to URL {0} for registering trigger. Body = {1}, '
                  'headers = {2}.\n'.format(url, payload, headers))

        post_resp = requests.post(url, data=json.dumps(payload),
                                  headers=headers,
                                  verify=dev-github_SSL_VERIFY)
    except:
        traceback.print_exc(limit=20)
        raise Exception('Unable to connect to dev-github endpoint {0}.'.format(url))
    else:
        status = post_resp.status_code
        if status in UNREACHABLE_CODES:
            msg = 'Got response {0}. Invalid triggers endpoint {1}.' \
                'Check configuration!'.format(status, url)
            raise Exception(msg)

        if status not in OK_CODES:
            msg = 'Failed to register trigger type {0}.{1} with dev-github. ' \
                'HTTP_CODE: {2}'.format(dev-github_TRIGGERTYPE_PACK,
                                        dev-github_TRIGGERTYPE_NAME, status)
            raise Exception(msg)
        else:
            print('Registered trigger type with dev-github.\n')


def _get_auth_url():
    return urljoin(dev-github_AUTH_BASE_URL, dev-github_AUTH_PATH)


def _get_auth_token(verbose=False):
    auth_url = _get_auth_url()

    if verbose:
        print('Will POST to URL {0} to get auth token.\n'.format(auth_url))

    try:
        resp = requests.post(auth_url, json.dumps({'ttl': 5 * 60}),
                             auth=(dev-github_USERNAME, dev-github_PASSWORD),
                             verify=dev-github_SSL_VERIFY)
    except:
        traceback.print_exc(limit=20)
        raise Exception('Unable to connect to dev-github endpoint {0}.'.
                        format(auth_url))
    else:
        if resp.status_code in UNREACHABLE_CODES:
            msg = 'Got response {0}. Invalid auth endpoint {1}. '\
                'Check configuration!'.format(resp.status_code, auth_url)
            raise Exception(msg)

        if resp.status_code not in OK_CODES:
            msg = 'Cannot get a valid auth token from {0}. '\
                'HTTP_CODE: {1}'.format(auth_url, resp.status_code)
            raise Exception(msg)

        return resp.json()['token']


def _get_dev-github_request_headers():
    headers = {}

    if not UNAUTHED:
        if IS_API_KEY_AUTH:
            headers[API_KEY_AUTH_HEADER] = dev-github_API_KEY
        else:
            if dev-github_AUTH_TOKEN:
                headers[TOKEN_AUTH_HEADER] = dev-github_AUTH_TOKEN
            else:
                pass

    return headers


def _register_with_dev-github(verbose=False):
    global REGISTERED_WITH_dev-github
    try:
        if not REGISTERED_WITH_dev-github:
            if verbose:
                print('Checking if trigger "{0}" registered with dev-github.'
                      .format(dev-github_TRIGGERTYPE_REF))
            _register_trigger_with_dev-github(verbose=verbose)
            REGISTERED_WITH_dev-github = True
    except:
        traceback.print_exc(limit=20)
        sys.stderr.write(
            'Failed registering with dev-github. Won\'t post event.\n')
        sys.exit(2)


def _register_trigger_with_dev-github(verbose=False):
    triggers_url = _get_dev-github_triggers_url()

    try:
        headers = _get_dev-github_request_headers()
        if verbose:
            print('Will GET from URL {0} for detecting trigger {1}.\n'
                  .format(triggers_url, dev-github_TRIGGERTYPE_REF))
            print('Request headers: {0}\n'.format(headers))

        get_resp = requests.get(triggers_url, headers=headers,
                                verify=dev-github_SSL_VERIFY)

        if get_resp.status_code != httplib.OK:
            _create_trigger_type(verbose=verbose)
        else:
            body = json.loads(get_resp.text)
            if len(body) == 0:
                _create_trigger_type(verbose=verbose)
    except:
        traceback.print_exc(limit=20)
        raise Exception('Unable to connect to dev-github endpoint {0}.\n'
                        .format(triggers_url))
    else:
        if verbose:
            print('Successfully registered trigger {0} with dev-github.\n'
                  .format(dev-github_TRIGGERTYPE_REF))


def _get_dev-github_triggers_base_url():
    url = urljoin(dev-github_API_BASE_URL, dev-github_TRIGGERS_PATH)
    return url


def _get_dev-github_triggers_url():
    url = urljoin(_get_dev-github_triggers_base_url() + '/', dev-github_TRIGGERTYPE_REF)
    return url


def _get_dev-github_webhooks_url():
    url = urljoin(dev-github_API_BASE_URL, dev-github_WEBHOOKS_PATH)
    return url


def _post_webhook(url, body, verbose=False):
    headers = _get_dev-github_request_headers()
    headers['X-dev-github-Integration'] = 'nagios.'
    headers['Content-Type'] = 'application/json; charset=utf-8'

    try:
        if verbose:
            print('Webhook POST: url: {0}, headers: {1}, body: {2}\n'
                  .format(url, headers, body))
        r = requests.post(url, data=json.dumps(body), headers=headers,
                          verify=False)
    except:
        traceback.print_exc(10)
        raise Exception('Cannot connect to dev-github endpoint {0}.'.format(url))
    else:
        status = r.status_code

        if status in UNREACHABLE_CODES:
            msg = 'Webhook URL {0} does not exist. Check StackStorm '\
                'installation!'.format(url)
            raise Exception(msg)

        if status not in OK_CODES:
            sys.stderr.write('Failed posting nagio event to dev-github. HTTP_CODE: '
                             '{0}\n'.format(status))
        else:
            sys.stdout.write('Sent nagios event to dev-github. HTTP_CODE: '
                             '{0}\n'.format(status))


def _post_event_to_dev-github(payload, verbose=False):
    body = {}
    body['trigger'] = dev-github_TRIGGERTYPE_REF
    body['payload'] = payload

    try:
        _post_webhook(url=_get_dev-github_webhooks_url(), body=body, verbose=verbose)
        return True
    except:
        traceback.print_exc(limit=10)
        print('Cannot send event to dev-github.')
        sys.exit(3)


def _set_config_opts(config_file, verbose=False):
    global dev-github_USERNAME
    global dev-github_PASSWORD
    global dev-github_API_KEY
    global dev-github_AUTH_TOKEN
    global dev-github_API_BASE_URL
    global dev-github_AUTH_BASE_URL
    global dev-github_SSL_VERIFY
    global UNAUTHED
    global IS_API_KEY_AUTH
    if not os.path.exists(config_file):
        print('Configuration file "{0}" not found. Exiting!!!'
              .format(config_file))
        sys.exit(2)

    with open(config_file) as f:
        config = yaml.safe_load(f)

        if verbose:
            print('Contents of config file: {0}'.format(config))

        dev-github_USERNAME = config['dev-github_username']
        dev-github_PASSWORD = config['dev-github_password']
        dev-github_API_KEY = config.get('dev-github_api_key', None)
        dev-github_API_BASE_URL = config['dev-github_api_base_url']
        if not dev-github_API_BASE_URL.endswith('/'):
            dev-github_API_BASE_URL += '/'
        dev-github_AUTH_BASE_URL = config['dev-github_auth_base_url']
        if not dev-github_AUTH_BASE_URL.endswith('/'):
            dev-github_AUTH_BASE_URL += '/'
        UNAUTHED = config['unauthed']
        dev-github_SSL_VERIFY = config['ssl_verify']

    if dev-github_API_KEY:
        IS_API_KEY_AUTH = True

    if verbose:
        print('Unauthed? : {0}\nAPI key auth?: {1}\nSSL Verify? : {2}\n'
              .format(UNAUTHED, IS_API_KEY_AUTH, dev-github_SSL_VERIFY))

    if not UNAUTHED and not IS_API_KEY_AUTH:
        try:
            if not dev-github_AUTH_TOKEN:
                if verbose:
                    print('No auth token found. Let\'s get one from'
                          'StackStorm!')
                dev-github_AUTH_TOKEN = _get_auth_token(verbose=verbose)
        except:
            traceback.print_exc(limit=20)
            print('Unable to negotiate an auth token. Exiting!')
            sys.exit(1)


def _from_arg_to_payload(nagios_args):
    try:
        event_id = nagios_args[0]
        service = nagios_args[1]
        state = nagios_args[2]
        state_id = nagios_args[3]
        state_type = nagios_args[4]
        attempt = nagios_args[5]
        host = nagios_args[6]
    except IndexError:
        traceback.print_exc(limit=20)
        print('Number of Arguments given to the handler are incorrect')
        sys.exit(1)

    payload = {}
    payload['host'] = host
    payload['service'] = service
    payload['event_id'] = event_id
    payload['state'] = state
    payload['state_id'] = state_id
    payload['state_type'] = state_type
    payload['attempt'] = attempt
    payload['msg'] = STATE_MESSAGE.get(state, 'Undefined state.')
    return payload


def main(config_file, payload, verbose=False):

    _set_config_opts(config_file=config_file, verbose=verbose)
    _register_with_dev-github(verbose=verbose)
    _post_event_to_dev-github(payload, verbose=verbose)


if __name__ == '__main__':
    description = '\nStackStorm nagios event handler. Please provide args '\
        'in following order after the config_path:\n\n event_id, service, '\
        'state,state_id, state_type, attempt, host\n'

    parser = argparse.ArgumentParser(description)
    parser.add_argument('config_path',
                        help='Exchange to listen on')
    parser.add_argument('--verbose', '-v', required=False, action='store_true',
                        help='Verbose mode.')

    args, nagios_args = parser.parse_known_args()
    payload = _from_arg_to_payload(nagios_args)

    main(config_file=args.config_path, payload=payload, verbose=args.verbose)