from enum import Enum
from pathlib import Path
from typing import Awaitable, Callable, Optional, Union

from databases import Database
from loguru import logger
from pydantic import BaseConfig, BaseModel
from sqlalchemy import MetaData

from aopi_index_builder.exceptions import UserHasNoPermissions, UserWasNotFound


class AopiContextBase(BaseModel):
    """
    :database: context to use databases.
    :metadata: sqlalchemy metadata for table creation.
    :main_dir: directory to store packages.
    """

    database: Database
    metadata: MetaData
    main_dir: Path
    enable_users: bool
    get_user_id_function: Callable[["AopiContextBase", str, str], Awaitable[int]]
    check_user_permission: Callable[
        ["AopiContextBase", str, Optional[int], Union[str, Enum]], Awaitable[bool]
    ]

    class Config(BaseConfig):
        arbitrary_types_allowed = True
        allow_mutation = False


class PackageContext(BaseModel):
    """
    :prefix: base url prefix
    :packages_dir: your own directory to store packages.
    """

    prefix: str
    package_name: str
    packages_dir: Path

    class Config(BaseConfig):
        allow_mutation = False


class AopiContext(AopiContextBase, PackageContext):
    async def get_user_id(self, username: str, password: str) -> Optional[int]:
        """
        Get user id by username and password.

        This function will look up user by credentials in aopi database.
        If user system is disabled by aopi, then None would be returned.
        If user was not found ..py:exception::`UserWasNotFound`
        exception would be raised.

        :param username: user's username
        :param password: user's password
        :return: id, None or exception
        :exception: UserWasNotFound
        """
        if not self.enable_users:
            return None
        user_id = None
        try:
            user_id = await self.get_user_id_function(username, password)
        except Exception as e:
            logger.exception(e)
        if user_id is None:
            raise UserWasNotFound()
        return user_id

    async def has_permission(
        self, user_id: Optional[int], role: Union[str, Enum]
    ) -> None:
        """
        Check if user has permissions.
        You can pass either enum or name of the role to check.

        Usage is following:

            >>> from typing import Any
            >>> async def your_function() -> Any:
            >>>     context = get_context()
            >>>     uid = await context.get_user_id("username", "password")
            >>>     await context.has_permission(uid, "role")
            >>>     ... # do something, you're safe

        The key thing is that if user has no permission or either cannot be found
        the exception will stop your function from execution.

        :param user_id: user's unique id from aopi
        :param role: required role for action
        :return: bool or raise an exception
        :exception: UserHasNoPermissions
        """
        if not self.enable_users:
            return
        if user_id is None:
            raise UserHasNoPermissions()
        try:
            if not await self.check_user_permission(
                self.package_name,
                user_id,
                role.value if isinstance(role, Enum) else role,
            ):
                raise UserHasNoPermissions()
            return
        except Exception as e:
            logger.exception(e)
        except UserHasNoPermissions:
            pass
        raise UserHasNoPermissions()

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
