# region Imports

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from core.utils import get_time

# endregion
# region Pydantic Models


class StreamingServiceResponse(BaseModel):
    """
    Pydantic model representing a response from a streaming service.
    Attributes:
        status (str): The status of the response (e.g., 'success', 'error').
        message (Optional[str]): An optional message providing additional information.
    """

    status: str = Field(
        ..., description="The status of the response (e.g., 'success', 'error')"
    )
    message: Optional[str] = Field(
        None, description="An optional message providing additional information"
    )


class PathRecord(BaseModel):
    """
    Pydantic model representing a file system path record.
    Attributes:
        id (Optional[int]): The unique identifier of the path record.
        path (str): The file system path.
        description (Optional[str]): An optional description of the path.
    """

    id: Optional[int] = Field(
        None, description="The unique identifier of the path record"
    )
    path: str = Field(..., description="The file system path")
    description: Optional[str] = Field(
        None, description="An optional description of the path"
    )
    record_type: Optional[str] = Field(
        None, description="The type of the path record (e.g., 'file', 'directory')"
    )
    added_at: Optional[datetime] = Field(
        default=get_time(), description="Timestamp of when the path record was added"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp of the last update to the path record"
    )

    def update(self) -> None:
        """Update the updated_at timestamp to the current time."""
        self.updated_at = get_time()


# endregion
