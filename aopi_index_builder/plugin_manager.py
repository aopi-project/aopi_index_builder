from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

from aopi_index_builder import AopiContextBase, PluginInfo, init_context, load_plugins
from aopi_index_builder.exceptions import UserError
from aopi_index_builder.schema import (
    PackageVersion,
    PluginFullPackageInfo,
    PluginPackagePreview,
)
from aopi_index_builder.utils import run_smart_async


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
        self.plugins_map = {plugin.package_name: plugin for plugin in plugins}

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

    def get_languages(self) -> List[str]:
        return list(
            map(lambda x: x.package_index.target_language, self.plugins_map.values())
        )

    async def find_package(
        self,
        *,
        user_id: Optional[int],
        package_name: str,
        limit: int,
        page: int,
        language: Optional[str] = None,
    ) -> List[PluginPackagePreview]:
        plugins_count = len(self.plugins_map.values())
        packages: List[PluginPackagePreview] = list()
        plugin_limit = limit // plugins_count
        offset = plugin_limit * page
        for plugin in self.plugins_map.values():
            if (
                language is not None
                and plugin.package_index.target_language.lower() != language.lower()
            ):
                continue
            func = plugin.package_index.__dict__["find_packages_func"]
            try:
                plugin_packages = await run_smart_async(
                    func, user_id, package_name, plugin_limit, offset
                )
                packages.extend(
                    map(
                        lambda package: PluginPackagePreview(
                            **package.dict(),
                            plugin_name=plugin.package_name,
                            language=plugin.package_index.target_language,
                        ),
                        plugin_packages,
                    )
                )
            except UserError as e:
                logger.debug(e)
                continue
        return packages

    async def get_package_versions(
        self, *, user_id: Optional[int], plugin_name: str, package_id: Any
    ) -> List[PackageVersion]:
        plugin = self.plugins_map.get(plugin_name)
        if not plugin:
            return list()
        func = plugin.package_index.__dict__["get_versions_func"]
        try:
            return await run_smart_async(func, user_id, package_id)
        except UserError as e:
            logger.debug(e)
        return list()

    async def get_package_info(
        self, *, user_id: str, plugin_name: str, package_id: Any
    ) -> Optional[PluginFullPackageInfo]:
        plugin = self.plugins_map.get(plugin_name)
        if not plugin:
            return None
        func = plugin.package_index.__dict__["get_package_info_func"]
        try:
            package_info = await run_smart_async(func, user_id, package_id)
            return PluginFullPackageInfo(
                **package_info.dict(),
                plugin_name=plugin.package_name,
                language=plugin.package_index.target_language,
            )
        except UserError as e:
            logger.debug(e)
        return None

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
