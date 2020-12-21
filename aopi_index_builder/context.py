from pathlib import Path
from typing import Optional

from databases import Database
from pydantic import BaseConfig, BaseModel
from sqlalchemy import MetaData


class AopiContextBase(BaseModel):
    database: Database
    metadata: MetaData
    main_dir: Path

    class Config(BaseConfig):
        arbitrary_types_allowed = True
        allow_mutation = False


class PackageContext(BaseModel):
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
    global __base_ctx
    __base_ctx = base


def get_base_ctx() -> AopiContextBase:
    global __base_ctx
    if __base_ctx is None:
        raise ValueError("Base context is not initialized.")
    return __base_ctx


def init_package_ctx(ctx: PackageContext) -> None:
    global __package_ctx
    __package_ctx = ctx


def get_context() -> AopiContext:
    base_ctx = get_base_ctx()
    global __package_ctx
    if __package_ctx is None:
        raise ValueError("Context is not initialized.")

    return AopiContext(**base_ctx.dict(), **__package_ctx.dict())
