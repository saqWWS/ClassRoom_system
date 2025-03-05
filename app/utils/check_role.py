from app.database.mongoDB import collection_users
from app.models.users import Role


async def verify_user_role(api_key: str):
  user = await collection_users.find_one({"api_key": api_key})

  if not user:
    return None

  role = user.get("role")

  if role in [r.value for r in Role]:
    return Role(role)

  return None
