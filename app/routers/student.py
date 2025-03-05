import json

from quart import jsonify, Blueprint, request, websocket

from app.schemas.students import BookingNotification
from app.services.student_service import StudentService
from app.utils.send_to_admin import broadcast_to_admins, send_slack_message, active_connections_st

router = Blueprint("classroom", __name__, url_prefix="/classroom")


@router.route("/", methods=["GET"])
async def get_all_rooms():
  all_rooms = await StudentService.get_all_rooms()
  return jsonify(all_rooms)


@router.route("/room", methods=["GET"])
async def get_room():
  room_name = request.args.get("room_name")
  room_type = request.args.get("room_type")

  try:
    filtered_rooms = await StudentService.filtered_rooms(room_name, room_type)
    return filtered_rooms

  except Exception as e:
    return jsonify({"error": str(e)})


@router.websocket("/ws")
async def student_ws_connection():
  api_key = websocket.headers.get("X-API-Key")
  if not api_key:
    await websocket.send_json({"error": "API key is required"}), 400

  conn = websocket._get_current_object()
  active_connections_st.add(conn)
  from app.utils.storage_room import storage

  try:
    while True:
      message = await websocket.receive()
      try:
        message_dict = json.loads(message)
        booking_notification = BookingNotification(**message_dict)

        response, status_code = await StudentService.send_book_room_notification(booking_notification, api_key)
        storage.append(response)
        if status_code != 200:
          await websocket.send_json({"error": response})
        else:
          await websocket.send_json({"success": response})
          await broadcast_to_admins(f"Notification from Student: {message}")
          slack_text = (f"📢 New Booking Notification!\n**Student:** "
                        f"{message_dict.get('student_name')}\n**Room:**"
                        f" {message_dict.get('room_number')}")
          await send_slack_message(slack_text)
      except:
        await websocket.send_json({"error": "Invalid arguments"})
        continue
  except Exception as e:
    await websocket.send_json({"error": f"Error with WebSocket connection: {str(e)}"})
  finally:
    active_connections_st.remove(conn)