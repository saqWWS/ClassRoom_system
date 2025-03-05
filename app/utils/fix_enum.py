from app.models.schedule import RoomsName, RoomType


def determine_room_type(room_name_enum: RoomsName):
  if room_name_enum in {RoomsName.ADA_LOVELACE, RoomsName.ALAN_TURING,
                        RoomsName.CLAUDE_SHANNON, RoomsName.DONALD_KNUTH,
                        RoomsName.LIBRARY, RoomsName.WILLIAM_SHOCKLEY}:
    return RoomType.CLASSROOMS
  elif room_name_enum in {RoomsName.SIRIUS, RoomsName.PROXIMA, RoomsName.DARTH_VADER}:
    return RoomType.MEETING_ROOMS
  elif room_name_enum in {RoomsName.RECORDING_ROOM, RoomsName.CALL_ROOM_N2}:
    return RoomType.OTHERS
