# region Docstring
"""
...
"""
# endregion
# region Imports
from logging import Logger
from core.database import DatabaseSessionGenerator
from core.models.repo import RepoEntity, RepoScanResult, Repo
from pydantic import BaseModel

# endregion


# region Image Importer Service
# region Result Models
class RepoImporterResult(BaseModel):
    success: bool
    message: str
    url: str


# endregion
