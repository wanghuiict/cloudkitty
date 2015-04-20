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
# @author: Stéphane Albert
#
import pecan
from pecan import rest
from stevedore import extension
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from cloudkitty.api.v1.datamodels import rating as rating_models
from cloudkitty.openstack.common import log as logging

LOG = logging.getLogger(__name__)

PROCESSORS_NAMESPACE = 'cloudkitty.rating.processors'


class ModulesController(rest.RestController):
    """REST Controller managing rating modules."""

    def __init__(self):
        self.extensions = extension.ExtensionManager(
            PROCESSORS_NAMESPACE,
            # FIXME(sheeprine): don't want to load it here as we just need the
            # controller
            invoke_on_load=True
        )

    @wsme_pecan.wsexpose(rating_models.CloudkittyModuleCollection)
    def get_all(self):
        """return the list of loaded modules.

        :return: name of every loaded modules.
        """
        modules_list = []
        for module in self.extensions:
            infos = module.obj.module_info.copy()
            infos['module_id'] = infos.pop('name')
            modules_list.append(rating_models.CloudkittyModule(**infos))

        return rating_models.CloudkittyModuleCollection(
            modules=modules_list)

    @wsme_pecan.wsexpose(rating_models.CloudkittyModule, wtypes.text)
    def get_one(self, module_id):
        """return a module

        :return: CloudKittyModule
        """
        try:
            module = self.extensions[module_id]
        except KeyError:
            pecan.abort(404, 'Module not found.')
        infos = module.obj.module_info.copy()
        infos['module_id'] = infos.pop('name')
        return rating_models.CloudkittyModule(**infos)

    @wsme_pecan.wsexpose(rating_models.CloudkittyModule,
                         wtypes.text,
                         body=rating_models.CloudkittyModule,
                         status_code=302)
    def put(self, module_id, module):
        """Change the state and priority of a module.

        :param module_id: name of the module to modify
        :param module: CloudKittyModule object describing the new desired state
        """
        try:
            ext = self.extensions[module_id].obj
        except KeyError:
            pecan.abort(404, 'Module not found.')
        if ext.enabled != module.enabled:
            ext.set_state(module.enabled)
        if ext.priority != module.priority:
            ext.set_priority(module.priority)
        pecan.response.location = pecan.request.path


class UnconfigurableController(rest.RestController):
    """This controller raises an error when requested."""

    @wsme_pecan.wsexpose(None)
    def put(self):
        self.abort()

    @wsme_pecan.wsexpose(None)
    def get(self):
        self.abort()

    def abort(self):
        pecan.abort(409, "Module is not configurable")


class ModulesExposer(rest.RestController):
    """REST Controller exposing rating modules.

    This is the controller that exposes the modules own configuration
    settings.
    """

    def __init__(self):
        self.extensions = extension.ExtensionManager(
            PROCESSORS_NAMESPACE,
            # FIXME(sheeprine): don't want to load it here as we just need the
            # controller
            invoke_on_load=True
        )
        self.expose_modules()

    def expose_modules(self):
        """Load rating modules to expose API controllers."""
        for ext in self.extensions:
            # FIXME(sheeprine): we should notify two modules with same name
            if not hasattr(self, ext.name):
                if not ext.obj.config_controller:
                    ext.obj.config_controller = UnconfigurableController
                setattr(self, ext.name, ext.obj.config_controller())


class RatingController(rest.RestController):
    """The RatingController is exposed by the API.

    The RatingControler connects the ModulesExposer, ModulesController
    and a quote action to the API.
    """

    _custom_actions = {
        'quote': ['POST'],
    }

    modules = ModulesController()
    module_config = ModulesExposer()

    @wsme_pecan.wsexpose(float,
                         body=rating_models.CloudkittyResourceCollection)
    def quote(self, res_data):
        """Get an instant quote based on multiple resource descriptions.

        :param res_data: List of resource descriptions.
        :return: Total price for these descriptions.
        """
        client = pecan.request.rpc_client.prepare(namespace='rating')
        res_dict = {}
        for res in res_data.resources:
            if res.service not in res_dict:
                res_dict[res.service] = []
            json_data = res.to_json()
            res_dict[res.service].extend(json_data[res.service])

        res = client.call({}, 'quote', res_data=[{'usage': res_dict}])
        return res