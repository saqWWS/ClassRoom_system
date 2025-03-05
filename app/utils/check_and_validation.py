import re

from quart import jsonify

from app.database.mongoDB import collection_users


async def check_valid_name(name: str):
  name_regex = r"^[a-zA-Z]{3,50}$"
  if not re.match(name_regex, name):
    return jsonify({"message": "Name must contain only letters "
                               "and be between 3 and 50 characters"}), 400
  return None


async def check_valid_surname(surname: str):
  surname_regex = r"^[a-zA-Z]{3,50}$"
  if not re.match(surname_regex, surname):
    return jsonify({"message": "Surname must contain only letters "
                               "and be between 3 and 50 characters"}), 400
  return None


async def check_valid_group_name(group_name: str):
  group_name_regex = r"^[a-zA-Z0-9/]{2,20}$"
  if not re.match(group_name_regex, group_name):
    return jsonify({
      "message": "Group name must contain only letters, numbers, and '/' "
                 "character, and be between 3 and 50 characters"}), 400
  return None


async def check_valid_email(email: str):
  email_regex = r"(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)"
  if not re.match(email_regex, email):
    return jsonify({"message": "Invalid email address"}), 400
  return None


async def check_valid_phone_number(phone_number: str):
  phone_number_regex = r"^\+?\d{10,15}$"
  if not re.match(phone_number_regex, phone_number):
    return jsonify({"message": "Phone number must contain only digits and be 10-15 characters long"}), 400
  return None


async def check_email_exists(email: str):
  user = await collection_users.find_one({"email": email})
  if user:
    return jsonify({"message": "Email already exists"}), 400
  return None


async def check_phone_number_exists(phone_number: str):
  user = await collection_users.find_one({"phone_number": phone_number})
  if user:
    return jsonify({"message": "Phone number already exists"}), 400
  return None
