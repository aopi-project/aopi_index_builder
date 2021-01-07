import io
import os
from contextlib import redirect_stdout
from enum import Enum
from typing import Any, Awaitable, Callable, List, Optional, Type, Union

import entrypoints
from fastapi import APIRouter
from loguru import logger
from pydantic import BaseConfig, BaseModel

from aopi_index_builder.context import PackageContext, get_base_ctx, init_package_ctx
from aopi_index_builder.schema import FullPackageInfo, PackagePreview, PackageVersion


class PackageIndex(BaseModel):
    """
    The main class for creating new package indices.
    """

    router: APIRouter
    target_language: str
    db_models: List[Type[Any]] = []
    roles: Type[Enum]
    plugin_help: Optional[str] = None
    find_packages_func: Callable[
        [Optional[int], str, int],
        Union[Awaitable[List[PackagePreview]], List[PackagePreview]],
    ]
    get_package_info_func: Callable[
        [Optional[int], Any], Union[Awaitable[FullPackageInfo], List[FullPackageInfo]]
    ]
    get_versions_func: Callable[
        [Optional[int], Any],
        Union[Awaitable[List[PackageVersion]], List[PackageVersion]],
    ]

    def __init__(
        self,
        router: APIRouter,
        target_language: str,
        roles: Type[Enum],
        find_packages_func: Callable[
            [Optional[int], str, int],
            Union[Awaitable[List[PackagePreview]], List[PackagePreview]],
        ],
        get_package_info_func: Callable[
            [Optional[int], Any],
            Union[Awaitable[FullPackageInfo], List[FullPackageInfo]],
        ],
        get_versions_func: Callable[
            [Optional[int], Any],
            Union[Awaitable[List[PackageVersion]], List[PackageVersion]],
        ],
        db_models: Optional[List[Type[Any]]] = None,
        plugin_help: Optional[str] = None,
    ):
        """
        Package index constructor.
        You must return instance of this class when creating new package index.

        :param router: router for package index api.
            All this routes appending to aopi routes to be used for integration with
            package managers.
        :param target_language: Name of target language or technology.
        :param roles: Roles for aopi rbac system to be used in this plugin.
        :param find_packages_func: function to find package in index.
            This function takes 4 positional arguments:
                * "current_user_id": Optional[int]
                * "package_name": str
                * "limit": int
                * "offset": int
        :param get_package_info_func: function to get full information about package.
            This function takes two arguments:
                * "current_user_id": Optional[int]
                * "package_id": Any.
        :param get_versions_func: function to get all versions of specific package.
            it takes two positional arguments:
                * "current_user_id": Optional[int]
                * "package_id": Any.
        :param db_models: used in this plugin.
            This thing is made to be sure, that all models for every plugin are created.
        :param plugin_help: This string is used as help
            for user about how to use provided api.
            For example:
            "To use aopi_python install packages as the following:
            pip install --index-url http://{aopi_url}/python/simple"

        """
        super(PackageIndex, self).__init__(
            router=router,
            target_language=target_language,
            roles=roles,
            db_models=db_models or [],
            plugin_help=plugin_help,
            find_packages_func=find_packages_func,
            get_package_info_func=get_package_info_func,
            get_versions_func=get_versions_func,
        )

    class Config(BaseConfig):
        arbitrary_types_allowed = True


class PluginInfo(BaseModel):
    prefix: str
    plugin_name: str
    roles: List[str]
    package_name: str
    package_version: str
    package_index: PackageIndex


def load_plugins() -> List[PluginInfo]:
    """
    Discover and load all plugins available in
    current environment.

    """
    indices = []
    base_ctx = get_base_ctx()
    for entrypoint in entrypoints.get_group_all("aopi_index"):
        plugin_name = entrypoint.name
        plugin_distro = entrypoint.distro
        plugin_package_dir = base_ctx.main_dir.joinpath(plugin_name)
        if not plugin_package_dir.exists():
            os.makedirs(plugin_package_dir)
        plugin_prefix = f"/{plugin_name}"
        init_package_ctx(
            PackageContext(
                prefix=plugin_prefix,
                package_name=plugin_distro.name,
                packages_dir=plugin_package_dir,
            )
        )
        logger.debug(f"Loading {plugin_name}")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            try:
                index_factory = entrypoint.load()
                index = index_factory()
                if not isinstance(index, PackageIndex):
                    logger.error("Plugin has returned wrong type.")
                    logger.debug(f"Expected: PackageIndex. Actual: {index.__class__}")
                    continue
                indices.append(
                    PluginInfo(
                        prefix=plugin_prefix,
                        plugin_name=plugin_name,
                        roles=[role.value for role in index.roles],
                        package_name=plugin_distro.name,
                        package_version=plugin_distro.version,
                        package_index=index,
                    )
                )
            except Exception as e:
                logger.error(f"Can't load plugin {plugin_name}")
                logger.exception(e)
            logger.debug(f"{plugin_name} captured output: \n{buffer.getvalue()}")
    return indices
