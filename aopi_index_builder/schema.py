from typing import Any, Dict, Optional

from pydantic import BaseModel


class PackagePreview(BaseModel):
    id: Any
    name: str
    short_description: Optional[str]


class FullPackageInfo(PackagePreview):
    description: Optional[str]
    metadata: Dict[str, str]
    last_version: str


class PackageVersion(BaseModel):
    version: str
    yanked: bool
    downloads: str
    metadata: Dict[str, str]
