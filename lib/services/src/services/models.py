from typing import Optional

from pydantic import BaseModel, Field


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
