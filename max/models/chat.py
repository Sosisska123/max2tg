from pydantic import BaseModel


class ChatModel(BaseModel):
    id: int
    title: str
    last_message_id: int
    messages_count: int
