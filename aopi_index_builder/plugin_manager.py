from typing import Dict, List

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

from aopi_index_builder import AopiContextBase, PluginInfo, init_context, load_plugins


class PluginRole(BaseModel):
    plugin_name: str
    role: str


class PluginManager:
    def __init__(self, context: AopiContextBase) -> None:
        self.context = context
        self.plugins_map: Dict[str, PluginInfo] = dict()

    def load(self) -> None:
        init_context(self.context)
        plugins = load_plugins()
        self.plugins_map = {plugin.plugin_name: plugin for plugin in plugins}

    def get_roles(self) -> List[PluginRole]:
        roles: List[PluginRole] = list()
        for plugin in self.plugins_map.values():
            roles.extend(
                map(
                    lambda x: PluginRole(plugin_name=plugin.package_name, role=x),
                    plugin.roles,
                )
            )
        return roles

    def add_routes(self, app: FastAPI) -> None:
        for plugin in self.plugins_map.values():
            index = plugin.package_index
            logger.debug(
                f"Enabling plugin {plugin.plugin_name} "
                f"from {plugin.package_name}:{plugin.package_version}"
            )
            app.include_router(
                router=index.router, prefix=plugin.prefix, tags=[plugin.package_name]
            )
