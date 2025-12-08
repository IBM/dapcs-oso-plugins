# Copyright (c) 2025 IBM Corp.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from flask import Flask
from flask_restx import Api

from oso_ripple_plugins.common import pre_request

from .config import BaseConfig


def create_app(config: object, app_name=None, root_path=None):

    if app_name is None:
        if config is None:
            app_name = BaseConfig.app_name
        elif config.app_name is not None:
            app_name = config.app_name
        else:
            app_name = BaseConfig.app_name

    if root_path is None:
        if config is None:
            root_path = BaseConfig.root_path
        elif config.root_path is not None:
            root_path = config.root_path
        else:
            root_path = BaseConfig.root_path

    app = Flask(__name__, instance_relative_config=True)

    configure_app(app, config)
    pre_request.configure_flask_common(app)
    configure_api(app)
    configure_logging(app)
    configure_backend_plugin_manager(app)

    return app


def configure_app(app: Flask, config: object):
    app.config.from_object(config)


def configure_api(app: Flask):
    from ..api.v1alpha1 import api as v1alpha1

    api = Api(
        title="My Title",
        version="1.0",
        description="A description",
    )

    api.add_namespace(v1alpha1, path="/api/backend/" + v1alpha1.name)
    api.init_app(app)


def configure_logging(app: Flask):
    return


def configure_backend_plugin_manager(app: Flask):
    from oso_ripple_plugins.backend_plugin.backend_plugin_manager import (
        BackendPluginManager,
    )

    app.bpm = BackendPluginManager()
