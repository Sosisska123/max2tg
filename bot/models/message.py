from pydantic import BaseModel


class Message(BaseModel):
    type: str


class RequestPhoneNumberModel(Message):
    type: str = "request_phone_number"


class ResponsePhoneNumberModel(Message):
    type: str = ""
