from quart import jsonify

from app.database.mongoDB import collection_users, collection_schedules
from app.models.schedule import Room, RoomsName, Schedule, RoomCapacity
from app.models.users import User, Role
from app.schemas.admin import Admin, DeleteStudent, CancelBooking
from app.schemas.admin import BookRoom
from app.schemas.students import Student
from app.utils.check_and_validation import check_email_exists, check_phone_number_exists
from app.utils.check_role import verify_user_role
from app.utils.fix_enum import determine_room_type
from app.utils.generate_key import generate_api_key
from app.utils.time_managment import is_time_valid, combine_date_and_time, is_room_available


class AdminService:
  @staticmethod
  async def get_all_students(api_key: str):
    admin = await verify_user_role(api_key)
    if not admin or admin != Role.ADMIN:
      return jsonify({"error": "Not authorized"}), 401

    students_cursor = collection_users.find({"role": Role.STUDENT.value})
    students_list = await students_cursor.to_list(length=None)

    if not students_list:
      return jsonify({"error": "Student not found"}), 404

    all_students = [
      Student.model_validate({**student, "_id": str(student["_id"])})
      .model_dump(by_alias=True, exclude_unset=True, exclude={"api_key"})
      for student in students_list
    ]

    return all_students

  @staticmethod
  async def get_student(api_key: str, filters: dict):
    admin = await verify_user_role(api_key)
    if not admin or admin != Role.ADMIN:
      return {"error": "Not authorized"}, 401

    allowed_fields = {"name", "email", "phone_number"}
    query = {key: value for key, value in filters.items() if key in allowed_fields}

    if not query:
      return {"error": "At least one search parameter is required"}, 400

    students_cursor = collection_users.find(query)
    students_list = await students_cursor.to_list(length=None)

    if not students_list:
      return {"error": "No student found"}, 404

    students = [
      Student.model_validate({**student, "_id": str(student["_id"])}).
      model_dump(by_alias=True, exclude_unset=True, exclude={"api_key"})
      for student in students_list
    ]

    return students, 200

  @staticmethod
  async def create_admin(data: dict, super_admin_api_key: str):
    user_role = await verify_user_role(super_admin_api_key)
    if not user_role or user_role != Role.SUPERADMIN:
      return jsonify(
        {"error": "Super admin API key is invalid or expired. "
                  "Please request a new one from the Super Admin."}), 401

    admin_api_key = generate_api_key()
    data["api_key"] = admin_api_key
    admin = Admin(**data)

    result = await collection_users.insert_one(admin.model_dump(by_alias=True, exclude={"id"}))

    if result.inserted_id:
      return jsonify({"message": "Admin successfully created",
                      "name": admin.name,
                      "api_key": admin_api_key}), 201

    return jsonify({"error": "Failed to create admin"}), 400

  @staticmethod
  async def create_student(data: dict, api_key: str):
    admin = await verify_user_role(api_key)
    if not admin or admin != Role.ADMIN:
      return jsonify({"error": "Not authorized"}), 401

    email = data.get("email")
    phone_number = data.get("phone_number")

    email_check = await check_email_exists(email)
    if email_check:
      return email_check

    phone_check = await check_phone_number_exists(phone_number)
    if phone_check:
      return phone_check

    student_api_key = generate_api_key()
    data["api_key"] = student_api_key
    student = Student(**data)
    new_student = student.model_dump(by_alias=True, exclude={"id"})
    db_model = User(**new_student).to_dict()

    result = await collection_users.insert_one(db_model)

    if result.inserted_id:
      return jsonify({"message": "Student was successfully created",
                      "name": student.name,
                      "api_key": student_api_key}), 201

    return jsonify({"error": "Failed to create student"}), 400

  @staticmethod
  async def delete_student(filters: DeleteStudent, api_key: str):
    admin = await verify_user_role(api_key)
    if not admin or admin != Role.ADMIN:
      return jsonify({"error": "Not authorized"}), 401

    deletable_fields = {"email", "api_key", "phone_number"}
    query = {key: value for key, value in filters.items() if key in deletable_fields}

    if not query:
      return {"error": "At least one search parameter is required"}, 400

    delete_result = await collection_users.delete_one(query)

    if delete_result.deleted_count == 0:
      return jsonify({"message": "No students found"}), 404

  @staticmethod
  async def book_room(data: BookRoom, api_key: str):
    admin = await verify_user_role(api_key)
    if not admin or admin != Role.ADMIN:
      return jsonify({"error": "Not authorized"}), 401

    try:
      date = data.date
      start = data.start_time
      end = data.end_time

      if not is_time_valid(start, end):
        return jsonify({"error": "Incorrect deadlines"}), 400

      date_time = combine_date_and_time(date, start, end)
      if not date_time:
        return jsonify({"error": "Incorrect date or time"}), 400

      start_datetime, end_datetime = date_time

      if not await is_room_available(data.room_name, start_datetime, end_datetime):
        return jsonify({"error": f"The room {data.room_name} "
                                 f"is occupied during the specified time period."}), 409

      if isinstance(data.room_name, str):
        normalized_room_name = data.room_name.replace(" ", "_").upper()
        if normalized_room_name in RoomsName.__members__:
          room_name_enum = RoomsName[normalized_room_name]
        else:
          return jsonify(f"Invalid room name provided: {data.room_name}"), 404
      else:
        room_name_enum = data.room_name

      room_type = determine_room_type(room_name_enum)
      capacity = RoomCapacity[room_name_enum.name].value

      room = Room(name=room_name_enum, room_type=room_type, capacity=capacity)
      schedule = Schedule(rooms=room,
                          start=start_datetime,
                          end=end_datetime,
                          group_name=data.group_name,
                          activity=data.activity,
                          status="confirmed")

      schedule_dict = schedule.to_dict()
      result = await collection_schedules.insert_one(schedule_dict)
      schedule_dict['_id'] = str(schedule_dict['_id'])

      return {**schedule_dict, "_id": str(result.inserted_id)}

    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @staticmethod
  async def cancel_room(cancel_room: CancelBooking, api_key: str):
    admin = await verify_user_role(api_key)
    if not admin or admin != Role.ADMIN:
      return jsonify({"error": "Not authorized"}), 401

    try:
      start_datetime, end_datetime = (
        combine_date_and_time(cancel_room.date, cancel_room.start, cancel_room.end))

      if not start_datetime or not end_datetime:
        return jsonify({"error": "Invalid date or time format."}), 400

      cancel = cancel_room.model_dump(by_alias=True)
      data = {
        "rooms.room_name": cancel["room_name"],
        "start": start_datetime,
        "end": end_datetime,
      }

      room_available = await is_room_available(cancel_room.room_name, start_datetime, end_datetime)
      if room_available:
        return jsonify({"error": "No matching booking found for cancellation."}), 404

      result = await collection_schedules.delete_one(data)

      if result.deleted_count == 0:
        return jsonify({"error": "No matching bookings found for cancellation."}), 404

      return jsonify({"success": f"{result.deleted_count} booking(s) deleted."}), 200

    except Exception as e:
      return jsonify({"error": str(e)}), 500
