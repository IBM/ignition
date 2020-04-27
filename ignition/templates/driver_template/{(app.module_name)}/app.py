import logging
import ignition.boot.api as ignition
import pathlib
import os
import {( app.module_name )}.config as driverconfig
{%- if app.is_resource_driver == true %}
from {( app.module_name )}.service.resourcedriver import ResourceDriverHandler
{%- endif %}


default_config_dir_path = str(pathlib.Path(driverconfig.__file__).parent.resolve())
default_config_path = os.path.join(default_config_dir_path, 'default_config.yml')


def create_app():
    app_builder = ignition.build_resource_driver('{( app.name )}')
    app_builder.include_file_config_properties(default_config_path, required=True)
    app_builder.include_file_config_properties('./{( app.module_name )}_config.yml', required=False)
    # custom config file e.g. for K8s populated from Helm chart values
    app_builder.include_file_config_properties('/var/{( app.module_name )}/{( app.module_name )}_config.yml', required=False)
    app_builder.include_environment_config_properties('{( app.module_name|upper )}_CONFIG', required=False)
    {%- if app.is_resource_driver == true %}
    app_builder.add_service(ResourceDriverHandler)
    {%- endif %}
    return app_builder.configure()


def init_app():
    app = create_app()
    return app.run()
