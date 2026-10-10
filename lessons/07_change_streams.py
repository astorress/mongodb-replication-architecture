# Lección 07 - Change streams: escuchar en tiempo real los cambios de una colección.
#
# Funcionan leyendo el oplog del replica set. Cada evento trae un resume token para continuar donde se quedó.
# Un insert trae el documento completo; un update trae solo los campos que cambiaron.
from lab.client import get_db
from lab.show import step, table, title

db = get_db()
employees = db.employees


def read(stream, count):
    events = []
    while len(events) < count:
        change = stream.try_next()
        if change is not None:
            events.append(change)
    return events


def describe(change):
    return {
        "operation": change["operationType"],
        "_id": str(change["documentKey"]["_id"])[-6:],
        "document": (change.get("fullDocument") or {}).get("name", "-"),
        "updated": change.get("updateDescription", {}).get("updatedFields", "-"),
    }


title("07 - Change streams")

employees.delete_many({"employee_id": "E9100"})

step("Abrir el stream y luego escribir: crear, ascender, subir salario y retirar a un empleado")
pipeline = [{"$match": {"operationType": {"$in": ["insert", "update", "delete"]}}}]
with employees.watch(pipeline, max_await_time_ms=500) as stream:
    employees.insert_one({"employee_id": "E9100", "name": "Camila Reyes", "email": "camila.reyes@company.com",
                          "department": "Marketing", "salary": 5_000_000})
    employees.update_one({"employee_id": "E9100"}, {"$set": {"title": "Líder de marketing"}})
    employees.update_one({"employee_id": "E9100"}, {"$inc": {"salary": 800_000}})
    employees.delete_one({"employee_id": "E9100"})

    table(describe(change) for change in read(stream, 2))
    token = stream.resume_token

step("El consumidor se detuvo tras 2 eventos. Reanudar con el resume token: llegan los que faltaban")
with employees.watch(pipeline, resume_after=token, max_await_time_ms=500) as stream:
    table(describe(change) for change in read(stream, 2))

print("\nUsos típicos: notificaciones, invalidar cachés, sincronizar con otros sistemas, auditoría.")
