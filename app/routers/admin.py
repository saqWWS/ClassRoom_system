import json

from quart import jsonify, Blueprint, request, websocket

from app.database.mongoDB import collection_schedules
from app.models.schedule import Schedule
from app.schemas.admin import BookRoom, CancelBooking
from app.services.admin_service import AdminService
from app.utils.check_and_validation import check_valid_name, check_valid_surname, check_valid_email, \
  check_valid_phone_number, check_valid_group_name
from app.utils.send_to_admin import active_connections_st

router = Blueprint("admin", __name__, url_prefix="/admin")


@router.route("/students", methods=["GET"])
async def get_all_students():
  try:
    api_key = request.headers.get("X-API-Key")

    if not api_key:
      return jsonify({"error": "API key is required"}), 400

    all_students = await AdminService.get_all_students(api_key)

    if isinstance(all_students, tuple):
      return jsonify(all_students[0]), all_students[1]

    return all_students

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.route("/get_student", methods=["POST"])
async def get_student():
  try:
    data = await request.json
    if not data:
      return jsonify({"error": "No data provided"}), 400

    api_key = request.headers.get("X-API-Key")

    if not api_key:
      return jsonify({"error": "API key is required"}), 400

    student_response, status_code = await AdminService.get_student(api_key, data)

    return jsonify(student_response), status_code

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.route("/create_admin", methods=['POST'])
async def create_admin_route():
  try:
    data = await request.json
    superadmin_api_key = request.headers.get('X-API-Key')

    if not superadmin_api_key:
      return jsonify({"error": "API key is missing"}), 400

    response = await AdminService.create_admin(data, superadmin_api_key)

    return response

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.route("/create_student", methods=['POST'])
async def create_student_route():
  try:
    data = await request.json
    admin_api_key = request.headers.get('X-API-Key')

    if not admin_api_key:
      return jsonify({"error": "API key is missing"}), 400

    validators = [
      await check_valid_name(data["name"]),
      await check_valid_surname(data["surname"]),
      await check_valid_email(data["email"]),
      await check_valid_phone_number(data["phone_number"]),
      await check_valid_group_name(data["group_name"]),
    ]

    error_response = next(filter(None, validators), None)
    if error_response:
      return error_response

    response = await AdminService.create_student(data, admin_api_key)

    return response

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.route("/delete_student", methods=["DELETE"])
async def delete_student():
  try:
    data = await request.json
    if not data:
      return jsonify({"error": "No data provided"}), 400

    api_key = request.headers.get("X-API-Key")
    if not api_key:
      return jsonify({"error": "API key is required"}), 400

    student_response = await AdminService.delete_student(data, api_key)

    if isinstance(student_response, tuple):
      return jsonify(student_response[0]), student_response[1]

    return jsonify({"message": "Student(s) deleted successfully"}), 200

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.route("/book_room", methods=["POST"])
async def book_room():
  try:
    data = await request.json
    if not data:
      return jsonify({"error": "No data provided"}), 400

    api_key = request.headers.get("X-API-Key")

    if not api_key:
      return jsonify({"error": "API key is required"}), 400

    book_room_data = BookRoom(**data)
    book_room_response = await AdminService.book_room(book_room_data, api_key)

    return book_room_response

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.route("/cancel_room", methods=["POST"])
async def cancel_room():
  try:
    data = await request.json
    if not data:
      return jsonify({"error": "No data provided"}), 400

    api_key = request.headers.get("X-API-Key")

    if not api_key:
      return jsonify({"error": "API key is required"}), 400

    cancel_data = CancelBooking(**data)
    cancel_room_response = await AdminService.cancel_room(cancel_data, api_key)

    return cancel_room_response

  except Exception as e:
    return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@router.websocket("/ws")
async def admin_ws_connection():
  conn = websocket._get_current_object()
  active_connections_st.add(conn)
  from app.utils.storage_room import storage

  try:
    while True:
      message = await websocket.receive()
      try:
        message_dict = json.loads(message)
        status = message_dict.get("status")

        try:
          booking_room = storage[0]
        except IndexError:
          await websocket.send_json({"error": "No booking request found"})
          continue

        if "schedule" not in booking_room or "rooms" not in booking_room["schedule"]:
          await websocket.send_json({"error": "Invalid booking data format"})
          continue

        if status == "confirmed":
          schedule_data = Schedule(
            status=status,
            rooms={
              "room_type": booking_room['schedule']['rooms']['room_type'],
              "name": booking_room['schedule']['rooms']['room_name'],
              "capacity": booking_room['schedule']['rooms']['capacity']
            },
            start=booking_room['schedule']['start'],
            end=booking_room['schedule']['end'],
            group_name=booking_room['schedule']['group_name'],
            activity=booking_room['schedule']['activity'],
          )

          schedule_data_dict = schedule_data.to_dict()
          result = await collection_schedules.insert_one(schedule_data_dict)
          schedule_data.id = str(result.inserted_id)

          storage.clear()

          await websocket.send_json({
            "info": "Booking confirmed",
            "schedule_id": schedule_data.id
          })

        elif status == "rejected":
          await websocket.send_json({"info": "Booking rejected"})

        else:
          await websocket.send_json({"error": "Invalid status value"})

      except json.JSONDecodeError:
        await websocket.send_json({"error": "Invalid JSON format"})

  finally:
    active_connections_st.remove(conn)
