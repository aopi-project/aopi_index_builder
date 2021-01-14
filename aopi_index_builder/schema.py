from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PluginInfo(BaseModel):
    plugin_name: str
    language: str


class PackagePreview(BaseModel):
    id: Any
    name: str
    short_description: Optional[str]


class PluginPackagePreview(PluginInfo, PackagePreview):
    ...


class ReadmeFormats(Enum, str):
    MD = "md"
    RST = "rst"
    TEXT = "text"


class FullPackageInfo(PackagePreview):
    description: Optional[str]
    description_format: ReadmeFormats = Field(ReadmeFormats.TEXT)
    metadata: Dict[str, Any]
    last_version: str


class PluginFullPackageInfo(PluginInfo, FullPackageInfo):
    ...


class PackageVersion(BaseModel):
    version: str
    yanked: bool
    metadata: Dict[str, Any]
