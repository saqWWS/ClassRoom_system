from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field


class Admin(BaseModel):
  name: str
  surname: str
  role: str
  api_key: str
  created_at: datetime = Field(default_factory=datetime.utcnow)

  class Config:
    populate_by_name = True
    json_encoders = {ObjectId: str}


class BookRoom(BaseModel):
  room_name: str
  start_time: str
  end_time: str
  date: str
  activity: str
  group_name: str
  created_at: datetime = Field(default_factory=datetime.utcnow)


class DeleteStudent(BaseModel):
  api_key: str
  email: str
  phone_number: str


class CancelBooking(BaseModel):
  room_name: str
  start: str
  end: str
  date: str
