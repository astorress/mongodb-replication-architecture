# Lección 02 - Consultas avanzadas e índices.
from datetime import timedelta

from lab.client import get_db
from lab.show import show, step, table, title

db = get_db()
employees = db.employees

title("02 - Consultas avanzadas")

step("Comparación y lógicos: salario entre 8 y 12 millones, en Bogotá o Medellín, activos")
query = {"salary": {"$gte": 8_000_000, "$lte": 12_000_000}, "city": {"$in": ["Bogotá", "Medellín"]}, "active": True}
print(employees.count_documents(query), "empleados")

step("$or: de Finanzas o con salario mayor a 17 millones")
query = {"$or": [{"department": "Finanzas"}, {"salary": {"$gt": 17_000_000}}]}
print(employees.count_documents(query), "empleados")

step("Arrays: skills contiene 'mongodb' / contiene todas ['python', 'aws'] / tiene exactamente 1 skill")
print("mongodb:", employees.count_documents({"skills": "mongodb"}))
print("python y aws:", employees.count_documents({"skills": {"$all": ["python", "aws"]}}))
print("una sola skill:", employees.count_documents({"skills": {"$size": 1}}))

step("$regex: nombres que empiezan por 'Val' (sin distinguir mayúsculas)")
print(employees.distinct("name", {"name": {"$regex": "^val", "$options": "i"}})[:5])

step("Fechas: contratados en el último año, ordenados por fecha")
since = employees.find_one(sort=[("hired_at", -1)])["hired_at"] - timedelta(days=365)
table(employees.find({"hired_at": {"$gte": since}}, {"_id": 0, "name": 1, "department": 1, "hired_at": 1})
      .sort("hired_at", -1).limit(5))

step("distinct: ciudades y cargos de Ingeniería")
print(employees.distinct("city"))
print(employees.distinct("title", {"department": "Ingeniería"}))

step("Paginación: página 3 de 5 elementos ordenados por employee_id")
print([e["employee_id"] for e in employees.find({}, {"employee_id": 1}).sort("employee_id").skip(10).limit(5)])


def plan(query):
    explain = db.command("explain", {"find": "employees", "filter": query}, verbosity="executionStats")
    stage, winning = [], explain["queryPlanner"]["winningPlan"]
    winning = winning.get("queryPlan", winning)
    while winning:
        stage.append(winning["stage"] + (f"({winning['indexName']})" if "indexName" in winning else ""))
        winning = winning.get("inputStage")
    stats = explain["executionStats"]
    return {"plan": " <- ".join(stage), "returned": stats["nReturned"], "docs_examined": stats["totalDocsExamined"]}


step("Índices: la misma consulta con y sin índice (explain)")
query = {"city": "Cali", "salary": {"$gt": 15_000_000}}
if "city_salary" in employees.index_information():
    employees.drop_index("city_salary")
show(plan(query))
employees.create_index([("city", 1), ("salary", -1)], name="city_salary")
show(plan(query))
print("Sin índice: COLLSCAN revisa todos los documentos. Con índice: IXSCAN revisa solo los que coinciden.")
