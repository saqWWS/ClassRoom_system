from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr

from app.models.schedule import ActivityType


class Student(BaseModel):
  name: str
  surname: str
  email: EmailStr
  phone_number: str
  group_name: str
  api_key: str
  created_at: datetime = Field(default_factory=datetime.utcnow)

  class Config:
    populate_by_name = True
    json_encoders = {ObjectId: str}


class BookingNotification(BaseModel):
  room_name: str
  start_time: str
  end_time: str
  date: str
  capacity: int
  activity: ActivityType
  group_name: str
  created_at: datetime = Field(default_factory=datetime.utcnow)

  class Config:
    populate_by_name = True
    json_encoders = {ObjectId: str}
