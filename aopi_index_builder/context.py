from pathlib import Path
from typing import Optional

from databases import Database
from pydantic import BaseConfig, BaseModel
from sqlalchemy import MetaData


class AopiContextBase(BaseModel):
    """
    :database: context to use databases.
    :metadata: sqlalchemy metadata for table creation.
    :main_dir: directory to store packages.
    """

    database: Database
    metadata: MetaData
    main_dir: Path

    class Config(BaseConfig):
        arbitrary_types_allowed = True
        allow_mutation = False


class PackageContext(BaseModel):
    """
    :prefix: base url prefix
    :packages_dir: your own directory to store packages.
    """

    prefix: str
    packages_dir: Path

    class Config(BaseConfig):
        allow_mutation = False


class AopiContext(AopiContextBase, PackageContext):
    class Config(BaseConfig):
        arbitrary_types_allowed = True


__base_ctx: Optional[AopiContextBase] = None
__package_ctx: Optional[PackageContext] = None


def init_context(base: AopiContextBase) -> None:
    """
    Initialize base context for plugins.

    This context parameters are the same for all plugins.
    And this context must be initialized manually in aopi application.

    :param base: this variable contains database and metadata for creating tables.
    """
    global __base_ctx
    __base_ctx = base


def get_base_ctx() -> AopiContextBase:
    """
    Just return the base context for all plugins.
    :return: context
    """
    global __base_ctx
    if __base_ctx is None:
        raise ValueError("Base context is not initialized.")
    return __base_ctx


def init_package_ctx(ctx: PackageContext) -> None:
    """
    This context is created for individual plugin.

    :param ctx: new package context.
    """
    global __package_ctx
    __package_ctx = ctx


def get_context() -> AopiContext:
    """
    Just returns the context for new plugin.

    It has base prefix for this plugin and
    packages dir specifically for current plugin. So you can store anything in it
    without breaking other plugins.

    You can call this function many times and your context will be the same.
    Also, you can't override your context. It's immutable for other plugins safety.

    :return: current plugin context.
    """
    base_ctx = get_base_ctx()
    global __package_ctx
    if __package_ctx is None:
        raise ValueError("Context is not initialized.")

    return AopiContext(**base_ctx.dict(), **__package_ctx.dict())
