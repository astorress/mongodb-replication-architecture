# Lección 01 - CRUD: crear, leer, actualizar y borrar documentos con pymongo.
from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from lab.client import get_db
from lab.show import show, step, title

db = get_db()
employees = db.employees

title("01 - CRUD")

employees.delete_many({"employee_id": {"$in": ["E9001", "E9002", "E9003"]}})

step("Create: insert_one (el driver genera _id si no se envía)")
result = employees.insert_one({
    "employee_id": "E9001",
    "name": "Laura Méndez",
    "email": "laura.mendez@company.com",
    "department": "Ingeniería",
    "title": "Desarrollador",
    "city": "Bogotá",
    "salary": 7_500_000,
    "skills": ["python", "mongodb"],
    "hired_at": datetime.now(timezone.utc),
    "active": True,
})
print("inserted_id:", result.inserted_id)

step("Create: insert_many")
employees.insert_many([
    {"employee_id": "E9002", "name": "Pedro Ruiz", "email": "pedro.ruiz@company.com", "department": "Ventas",
     "title": "Ejecutivo comercial", "city": "Cali", "salary": 4_200_000, "skills": ["crm"], "active": True},
    {"employee_id": "E9003", "name": "Marta Gil", "email": "marta.gil@company.com", "department": "Soporte",
     "title": "Agente de soporte", "city": "Medellín", "salary": 3_100_000, "skills": [], "active": True},
])

step("El índice único de email impide duplicados")
try:
    employees.insert_one({"employee_id": "E9999", "email": "laura.mendez@company.com"})
except DuplicateKeyError as error:
    print("DuplicateKeyError:", error.details["keyValue"])

step("Read: find_one con proyección (1 = incluir, 0 = excluir)")
show(employees.find_one({"employee_id": "E9001"}, {"_id": 0, "name": 1, "title": 1, "salary": 1}))

step("Read: find con filtro, orden y límite")
show(employees.find({"department": "Ingeniería", "city": "Bogotá"}, {"_id": 0, "name": 1, "salary": 1})
     .sort("salary", -1).limit(3))

step("Update: update_one con $set, $inc y $push")
result = employees.update_one(
    {"employee_id": "E9001"},
    {"$set": {"title": "Tech Lead"}, "$inc": {"salary": 1_000_000}, "$push": {"skills": "aws"}},
)
print("matched:", result.matched_count, "modified:", result.modified_count)

step("Update: find_one_and_update devuelve el documento ya actualizado")
show(employees.find_one_and_update({"employee_id": "E9002"}, {"$addToSet": {"skills": "excel"}},
                                   projection={"_id": 0, "name": 1, "skills": 1},
                                   return_document=ReturnDocument.AFTER))

step("Update: update_many - aumento de 200.000 a todo Soporte")
result = employees.update_many({"department": "Soporte"}, {"$inc": {"salary": 200_000}})
print("modificados:", result.modified_count)

step("Update: upsert - actualiza si existe, inserta si no")
result = employees.update_one({"employee_id": "E9004"},
                              {"$set": {"name": "Nuevo Ingreso", "email": "nuevo@company.com"}}, upsert=True)
print("upserted_id:", result.upserted_id)

step("Delete: delete_one y delete_many")
print("delete_one:", employees.delete_one({"employee_id": "E9004"}).deleted_count)
print("delete_many:", employees.delete_many({"employee_id": {"$in": ["E9001", "E9002", "E9003"]}}).deleted_count)
