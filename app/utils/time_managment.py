from datetime import datetime

import pytz

from app.database.mongoDB import collection_schedules

utc_timezone = pytz.UTC


def combine_date_and_time(date_str: str, start_str: str, end_str: str):
  try:
    current_year = datetime.now().year
    full_date = datetime.strptime(f"{date_str}.{current_year}", "%d.%m.%Y")

    start_time = datetime.strptime(start_str, "%H:%M").time()
    end_time = datetime.strptime(end_str, "%H:%M").time()

    start_datetime = datetime.combine(full_date.date(), start_time, tzinfo=utc_timezone)
    end_datetime = datetime.combine(full_date.date(), end_time, tzinfo=utc_timezone)

    return start_datetime, end_datetime
  except Exception:
    return None


def is_time_valid(start_str: str, end_str: str) -> bool:
  try:
    start_time = datetime.strptime(start_str, "%H:%M").time()
    end_time = datetime.strptime(end_str, "%H:%M").time()
    return start_time < end_time
  except Exception:
    return False


async def is_room_available(room_name: str, start_datetime: datetime, end_datetime: datetime):
  existing_book = await collection_schedules.find_one({
    "rooms.room_name": room_name,
    "$or": [
      {"start": {"$lt": end_datetime}, "end": {"$gt": start_datetime}},
      {"start": start_datetime, "end": end_datetime}
    ]
  })

  return existing_book is None
