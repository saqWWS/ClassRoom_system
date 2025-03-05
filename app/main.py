from quart import Quart
from quart_schema import QuartSchema

from app.routers.admin import router as admin_router
from app.routers.student import router as student_router

app = Quart(__name__)

QuartSchema(app)

app.register_blueprint(admin_router)
app.register_blueprint(student_router)

if __name__ == "__main__":
  app.run(debug=True)
