# Lección 00 - Cargar el conjunto de datos: la colección `employees` de la base `company`.
#
# La aplicación se conecta al replica set con la lista de nodos y el nombre del set (replicaSet=rs0).
# El driver descubre cuál es el PRIMARY y le envía las escrituras; los SECONDARY copian los datos solos.
import random
from datetime import datetime, timedelta, timezone

from lab.client import get_client
from lab.config import MONGO_DB
from lab.show import step, table, title

FIRST_NAMES = ["Ana", "Luis", "Carla", "Diego", "Elena", "Felipe", "Gina", "Hugo", "Isabel", "Jorge", "Karen",
               "Mateo", "Natalia", "Óscar", "Paula", "Ricardo", "Sofía", "Tomás", "Valentina", "Andrés"]
LAST_NAMES = ["Gómez", "Pérez", "Rodríguez", "Martínez", "López", "García", "Ramírez", "Torres", "Díaz",
              "Moreno", "Vargas", "Rojas", "Castro", "Ortiz", "Silva"]
DEPARTMENTS = {
    "Ingeniería": (["Desarrollador", "Tech Lead", "Arquitecto", "QA"], ["python", "java", "mongodb", "aws", "docker"]),
    "Ventas": (["Ejecutivo comercial", "Gerente de cuenta"], ["negociación", "crm", "excel"]),
    "Marketing": (["Analista de marketing", "Diseñador"], ["seo", "figma", "redes sociales", "excel"]),
    "Finanzas": (["Contador", "Analista financiero"], ["excel", "sql", "power bi"]),
    "Recursos Humanos": (["Analista de talento", "Generalista RRHH"], ["entrevistas", "excel", "nómina"]),
    "Soporte": (["Agente de soporte", "Coordinador de soporte"], ["atención al cliente", "crm", "sql"]),
}
CITIES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Cartagena"]
NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def employees(count=1000):
    rng = random.Random(42)
    docs = []
    for i in range(1, count + 1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        department = rng.choice(list(DEPARTMENTS))
        titles, skills = DEPARTMENTS[department]
        docs.append({
            "employee_id": f"E{i:04d}",
            "name": f"{first} {last}",
            "email": f"{first}.{last}.{i}@company.com".lower(),
            "department": department,
            "title": rng.choice(titles),
            "city": rng.choice(CITIES),
            "salary": rng.randrange(2_500_000, 18_000_000, 50_000),
            "skills": rng.sample(skills, rng.randint(1, len(skills))),
            "hired_at": NOW - timedelta(days=rng.randint(30, 3650)),
            "active": rng.random() > 0.08,
        })
    return docs


client = get_client()
db = client[MONGO_DB]

title("00 - Seed de la colección employees")

step(f"Borrando la base '{MONGO_DB}' (si existe) y creando employees")
client.drop_database(MONGO_DB)
result = db.employees.insert_many(employees())
print("insertados:", len(result.inserted_ids))

step("Índices: email único y departamento")
db.employees.create_index("email", unique=True)
db.employees.create_index("department")

step("Empleados por departamento")
table(db.employees.aggregate([
    {"$group": {"_id": "$department", "employees": {"$sum": 1}}},
    {"$sort": {"employees": -1}},
    {"$project": {"_id": 0, "department": "$_id", "employees": 1}},
]), ["department", "employees"])

step("Las escrituras fueron al PRIMARY; los SECONDARY ya tienen la misma copia")
print("PRIMARY:", client.primary, "| SECONDARY:", sorted(client.secondaries))
print("\nSiguiente: python lessons/01_crud.py")
