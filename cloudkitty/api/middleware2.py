# -*- coding: utf-8 -*-
# Copyright 2014 Objectif Libre
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
from oslo_config import cfg
from oslo_middleware import base
import webob
from oslo_log import log
from oslo_serialization import jsonutils
import requests
import six

LOG = log.getLogger(__name__)

class ServiceError(Exception):
    pass

class AuthCloudPlatformMiddleware(base.ConfigurableMiddleware):
    """
    It avoids authentication on public routes.
    """
    def __init__(self, app, conf, public_api_routes=[]):
        LOG.warning("wanghuiict: AuthCloudPlatformMiddleware __init__")
        self._public_routes = public_api_routes
        self._app = app
        super(AuthCloudPlatformMiddleware, self).__init__(app, conf)

    """ wanghuiict defined"""
    def process_request(self, req):
        LOG.warning('wanghuiict: AuthCloudPlatformMiddleware process_request')

    def _deny_request(self, code):
        """copy from keystonemiddleware/s3_token.py """
        error_table = {
            'AccessDenied': (401, 'Access denied'),
            'InvalidURI': (400, 'Could not parse the specified URI'),
        }
        resp = webob.Response(content_type='text/xml')
        resp.status = error_table[code][0]
        error_msg = ('<?xml version="1.0" encoding="UTF-8"?>\r\n'
                     '<Error>\r\n  <Code>%s</Code>\r\n  '
                     '<Message>%s</Message>\r\n</Error>\r\n' %
                     (code, error_table[code][1]))
        if six.PY3:
            error_msg = error_msg.encode()
        resp.body = error_msg
        return resp

    def _json_request(self, creds_json):
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.get('http://10.10.153.11:8765/api/auth/jwt/verify',
                                     headers=headers, data=creds_json,
                                     verify=False)
        except requests.exceptions.RequestException as e:
            LOG.warning('HTTP connection exception: %s', e)
            resp = self._deny_request('InvalidURI')
            raise ServiceError(resp)

        if response.status_code < 200 or response.status_code >= 300:
            LOG.warning('reply error: status=%s reason=%s',
                               response.status_code, response.reason)
            resp = self._deny_request('AccessDenied')
            raise ServiceError(resp)

        return response

    def _param_request(self, creds):
        try:
            response = requests.get('http://10.10.153.11:8765/api/auth/jwt/verify?token=%s' % creds,
                                     verify=False)
        except requests.exceptions.RequestException as e:
            LOG.warning('HTTP connection exception: %s', e)
            resp = self._deny_request('InvalidURI')
            raise ServiceError(resp)

        if response.status_code < 200 or response.status_code >= 300:
            LOG.warning('reply error: status=%s reason=%s',
                               response.status_code, response.reason)
            resp = self._deny_request('AccessDenied')
            raise ServiceError(resp)

        return response

    def __call__(self, environ, start_response):
        """Handle incoming request. authenticate and send downstream."""
        LOG.warning('wanghuiict: Calling AuthCloudPlatformMiddleware.')
        req = webob.Request(environ)
        token_id='0000000000000000000000000000000000000000000000000000000000000000000000000000'
        #token_id = req.headers.environ['HTTP_X_AUTH_TOKEN']
        try:
            token_id = req.headers['X-Auth-Token']
            #req.headers['authorization'] = token_id
        except KeyError as e:
            resp = self._deny_request('AccessDenied')
            LOG.warning('Received error, exiting middleware with KeyError: %s' % e.args[0])
            return resp(environ, start_response)
        """ HTTP_X_AUTH_TOKEN defined in ContextHook headers.environ 
            auth_token defined in credentials of cloudkitty.common.policy """
        LOG.warning('wanghuiict: AuthCloudPlatformMiddleware req.headers.environ %s' % token_id)

        # Authenticate request.
        creds = {'token': token_id}
        creds_json = jsonutils.dumps(creds)

        try:
            #resp = self._json_request(creds_json)
            resp = self._param_request(token_id)
        except ServiceError as e:
            resp = e.args[0]
            LOG.warning('Received error, exiting middleware with error: %s' % resp.status_code)
            return resp(environ, start_response)

        #response = req.get_response(self.application)
        #LOG.warning("wanghuiict: AuthCloudPlatformMiddleware response %s"%response)
        #return response
        return self._app(environ, start_response)

    #@webob.dec.wsgify
    def __call__2(self, req):
        LOG.warning("wanghuiict: AuthCloudPlatformMiddleware __call__, req.environ %s"%req.environ)
        token1 = req.environ.get('authorization', '0000000000000000000000000000000000000000000000000000000000000000000000000000')
        req.environ['authorization'] = token1
        response = req.get_response(self.application)

        return_headers = ['authorization', 'X-Auth-Token']

        for header in return_headers:
            if header not in response.headers:
                response.headers.add(header, token1)

        LOG.warning("wanghuiict: AuthCloudPlatformMiddleware response %s"%response)
        return response

    def __call__1(self, env, start_response):
        # Strip the / from the URL if we're not dealing with '/'
        path = env.get('PATH_INFO').rstrip('/') or '/'

        if path in self._public_routes:
            return self._app(env, start_response)

        return super(AuthCloudPlatformMiddleware, self).__call__(env, start_response)

    """
    @classmethod
    def factory(cls, global_config, **local_conf):
        public_routes = local_conf.get('acl_public_routes', '')
        public_api_routes = [path.strip() for path in public_routes.split(',')]

        def _factory(app):
            return cls(app, global_config, public_api_routes=public_api_routes)
        return _factory
    """
