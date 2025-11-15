from typing import Literal

from pydantic import BaseModel


class MediaModel(BaseModel):
    file_id: str
    file_type: Literal["photo", "doc", "video"]
