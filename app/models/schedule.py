from enum import Enum

from mongoengine import Document, EmbeddedDocument, StringField, IntField, DateTimeField, EnumField, \
  EmbeddedDocumentField


class ActivityType(Enum):
  MEETING = "Meeting"
  LECTURE = "Lecture"
  WORKSHOP = "Workshop"
  PROJECT = "Project"
  OTHER = "Other"


class RoomType(Enum):
  CLASSROOMS = "Classrooms"
  MEETING_ROOMS = "Meeting Rooms"
  OTHERS = "Others"


class RoomsName(Enum):
  ADA_LOVELACE = "Ada Lovelace"
  ALAN_TURING = "Alan Turing"
  CLAUDE_SHANNON = "Claude Shannon"
  DONALD_KNUTH = "Donald Knuth"
  LIBRARY = "Library"
  WILLIAM_SHOCKLEY = "William Shockley"

  DARTH_VADER = "Darth Vader"
  SIRIUS = "Sirius"
  PROXIMA = "Proxima"

  RECORDING_ROOM = "Recording Room"
  CALL_ROOM_N2 = "Call Room N2"


class RoomCapacity(Enum):
  ADA_LOVELACE = 70
  ALAN_TURING = 24
  CLAUDE_SHANNON = 32
  DONALD_KNUTH = 24
  WILLIAM_SHOCKLEY = 20
  LIBRARY = 30

  DARTH_VADER = 9
  SIRIUS = 6
  PROXIMA = 3

  RECORDING_ROOM = 2
  CALL_ROOM_N2 = 2


class Room(EmbeddedDocument):
  name = EnumField(RoomsName, required=True)
  room_type = EnumField(RoomType, required=True)
  capacity = IntField(required=True)

  def set_capacity(self):
    self.capacity = RoomCapacity[self.name].value


class Schedule(Document):
  rooms = EmbeddedDocumentField(Room, required=True)
  start = DateTimeField(required=True)
  end = DateTimeField(required=True)
  group_name = StringField(required=True)
  activity = EnumField(ActivityType, required=True)
  requested_capacity = IntField(required=True)
  status = StringField(choices=["pending", "confirmed", "rejected"], default="pending")

  def to_dict(self):
    return {
      "rooms": {
        "room_type": self.rooms.room_type.value if isinstance(self.rooms.room_type, Enum) else self.rooms.room_type,
        "room_name": self.rooms.name.value if isinstance(self.rooms.name, Enum) else self.rooms.name,
        "capacity": self.rooms.capacity,
      },
      "start": self.start,
      "end": self.end,
      "group_name": self.group_name,
      "activity": self.activity.value if isinstance(self.activity, Enum) else self.activity,
      "status": self.status
    }

  def is_capacity_sufficient(self):
    return self.requested_capacity <= self.rooms.capacity
