from typing import Any, Dict, Optional

from pydantic import BaseModel


class PluginInfo(BaseModel):
    plugin_name: str
    language: str


class PackagePreview(BaseModel):
    id: Any
    name: str
    short_description: Optional[str]


class PluginPackagePreview(PluginInfo, PackagePreview):
    ...


class FullPackageInfo(PackagePreview):
    description: Optional[str]
    metadata: Dict[str, str]
    last_version: str


class PluginFullPackageInfo(PluginInfo, FullPackageInfo):
    ...


class PackageVersion(BaseModel):
    version: str
    yanked: bool
    metadata: Dict[str, str]
