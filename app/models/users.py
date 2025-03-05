from datetime import datetime
from enum import Enum

from mongoengine import Document, StringField, EnumField, EmailField, DateTimeField


class Role(Enum):
  SUPERADMIN = "superadmin"
  ADMIN = "admin"
  STUDENT = "student"


class User(Document):
  name = StringField(required=True, max_length=50)
  surname = StringField(required=True, max_length=100)
  email = EmailField(required=True, unique=True)
  phone_number = StringField(required=True, max_length=20)
  role = EnumField(Role, required=True, default=Role.STUDENT)
  group_name = StringField(required=True, max_length=100)
  api_key = StringField(required=True, unique=True)
  created_at = DateTimeField(default=datetime.now())

  def to_dict(self):
    return {
      "name": self.name,
      "surname": self.surname,
      "email": self.email,
      "phone_number": self.phone_number,
      "role": self.role.value if isinstance(self.role, Enum) else self.role,
      "group_name": self.group_name,
      "api_key": self.api_key
    }

  meta = {"collection": "users"}
