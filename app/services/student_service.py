from collections import defaultdict

from quart import jsonify

from app.database.mongoDB import collection_schedules
from app.models.schedule import RoomsName, Room, Schedule, RoomCapacity
from app.models.users import Role
from app.schemas.students import BookingNotification
from app.utils.check_role import verify_user_role
from app.utils.fix_enum import determine_room_type
from app.utils.time_managment import is_time_valid, combine_date_and_time, is_room_available


class StudentService:
  @staticmethod
  async def get_all_rooms():
    all_rooms = await collection_schedules.find({}, {"_id": 0}).to_list(length=None)
    room_info = defaultdict(lambda: defaultdict(list))

    for schedule in all_rooms:
      room_data = schedule.get("rooms", {})
      room_type = room_data.get("room_type")
      room_name = room_data.get("room_name")

      if not room_type or not room_name:
        continue

      room_info[room_type][room_name].append({
        "start": schedule.get("start"),
        "end": schedule.get("end"),
        "group_name": schedule.get("group_name"),
        "activity": schedule.get("activity")
      })

    return room_info

  @staticmethod
  async def filtered_rooms(room_name, room_type):
    all_rooms = await StudentService.get_all_rooms()
    filtered_info = defaultdict(lambda: defaultdict(list))

    if not all_rooms:
      return jsonify({"message": "No rooms data available."}), 404

    for room_type_key, rooms in all_rooms.items():
      if room_type and room_type_key != room_type:
        continue

      for room_name_key, schedules in rooms.items():
        if room_name and room_name_key != room_name:
          continue

        filtered_info[room_type_key][room_name_key] = schedules

    if not filtered_info:
      return jsonify({"message": "No matching rooms found."}), 404

    filtered_info_dict = {k: dict(v) for k, v in filtered_info.items()}

    return filtered_info_dict

  @staticmethod
  async def send_book_room_notification(data: BookingNotification, api_key: str):
    student = await verify_user_role(api_key)
    if not student or student != Role.STUDENT:
      return {"error": "Not authorized"}, 401

    try:
      date = data.date
      start = data.start_time
      end = data.end_time

      if not is_time_valid(start, end):
        return {"error": "Incorrect deadlines"}, 400

      date_time = combine_date_and_time(date, start, end)
      if not date_time:
        return {"error": "Incorrect date or time"}, 400

      start_datetime, end_datetime = date_time

      is_available = await is_room_available(data.room_name, start_datetime, end_datetime)
      if not is_available:
        return {"error": f"The room {data.room_name} is occupied during the specified time period."}, 409

      if isinstance(data.room_name, str):
        normalized_room_name = data.room_name.replace(" ", "_").upper()
        if normalized_room_name in RoomsName.__members__:
          room_name_enum = RoomsName[normalized_room_name]
        else:
          return {"error": f"Invalid room name provided: {data.room_name}"}, 400
      else:
        room_name_enum = data.room_name

      room_type = determine_room_type(room_name_enum)
      max_capacity = RoomCapacity[room_name_enum.name].value
      requested_capacity = data.capacity

      if requested_capacity > max_capacity:
        return {"error": f"The room {data.room_name} has a maximum capacity of {max_capacity}. "
                         f"Requested: {requested_capacity}"}, 409

      room = Room(name=room_name_enum, room_type=room_type, capacity=requested_capacity)
      schedule = Schedule(
        rooms=room,
        start=start_datetime,
        end=end_datetime,
        group_name=data.group_name,
        activity=data.activity
      )

      schedule_dict = schedule.to_dict()

      return {"success": True, "schedule": schedule_dict}, 200

    except Exception as e:
      return {"error": str(e)}, 500
