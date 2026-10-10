# Lección 03 - Agregaciones: pipelines de etapas que transforman y resumen documentos.
from lab.client import get_db
from lab.show import step, table, title

db = get_db()
employees = db.employees

title("03 - Agregaciones")

step("Salario promedio, mínimo y máximo por departamento ($match -> $group -> $sort)")
table(employees.aggregate([
    {"$match": {"active": True}},
    {"$group": {"_id": "$department", "employees": {"$sum": 1}, "avg_salary": {"$avg": "$salary"},
                "min_salary": {"$min": "$salary"}, "max_salary": {"$max": "$salary"}}},
    {"$sort": {"avg_salary": -1}},
    {"$project": {"_id": 0, "department": "$_id", "employees": 1, "avg_salary": {"$round": ["$avg_salary", 0]},
                  "min_salary": 1, "max_salary": 1}},
]), ["department", "employees", "avg_salary", "min_salary", "max_salary"])

step("Contrataciones por año ($year)")
table(employees.aggregate([
    {"$group": {"_id": {"$year": "$hired_at"}, "hires": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
    {"$project": {"_id": 0, "year": "$_id", "hires": 1}},
]), ["year", "hires"])

step("Skills más comunes ($unwind: un documento por cada elemento del array)")
table(employees.aggregate([
    {"$unwind": "$skills"},
    {"$group": {"_id": "$skills", "employees": {"$sum": 1}}},
    {"$sort": {"employees": -1}},
    {"$limit": 5},
    {"$project": {"_id": 0, "skill": "$_id", "employees": 1}},
]), ["skill", "employees"])

step("Rangos salariales ($bucket)")
table(employees.aggregate([
    {"$bucket": {"groupBy": "$salary", "boundaries": [0, 5_000_000, 10_000_000, 15_000_000, 20_000_000],
                 "output": {"employees": {"$sum": 1}}}},
    {"$project": {"_id": 0, "from": "$_id", "employees": 1}},
]), ["from", "employees"])

step("Departamento x ciudad con más empleados ($group por dos campos)")
table(employees.aggregate([
    {"$group": {"_id": {"department": "$department", "city": "$city"}, "employees": {"$sum": 1}}},
    {"$sort": {"employees": -1}},
    {"$limit": 5},
    {"$project": {"_id": 0, "department": "$_id.department", "city": "$_id.city", "employees": 1}},
]), ["department", "city", "employees"])

step("$merge: guardar un reporte en otra colección (department_report)")
employees.aggregate([
    {"$group": {"_id": "$department", "payroll": {"$sum": "$salary"}, "employees": {"$sum": 1}}},
    {"$merge": {"into": "department_report", "whenMatched": "replace"}},
])
table(db.department_report.find().sort("payroll", -1), ["_id", "employees", "payroll"])
