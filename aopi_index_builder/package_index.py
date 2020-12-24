import io
import os
from contextlib import redirect_stdout
from typing import List, Optional, Type

import entrypoints
from fastapi import APIRouter
from loguru import logger
from orm import Model
from pydantic import BaseConfig, BaseModel

from aopi_index_builder.context import PackageContext, get_base_ctx, init_package_ctx


class PackageIndex(BaseModel):
    router: APIRouter
    models: List[Type[Model]] = []
    help: Optional[str] = None

    class Config(BaseConfig):
        arbitrary_types_allowed = True


class PluginInfo(BaseModel):
    prefix: str
    plugin_name: str
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
            PackageContext(prefix=plugin_prefix, packages_dir=plugin_package_dir)
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
                for model in index.models:
                    prefixed_name = f"{plugin_name}_{model.__table__.name}"
                    model.__table__.fullname = prefixed_name
                indices.append(
                    PluginInfo(
                        prefix=plugin_prefix,
                        plugin_name=plugin_name,
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
