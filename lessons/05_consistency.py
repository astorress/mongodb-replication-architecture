# Lección 05 - Write concern, read preference y read concern.
#
#   write concern   -> cuántos nodos deben confirmar una escritura antes de responder
#   read preference -> a qué nodo se envía una lectura
#   read concern    -> qué tan confirmados deben estar los datos que se leen
import time

from pymongo import ReadPreference, WriteConcern
from pymongo.errors import WriteConcernError
from pymongo.read_concern import ReadConcern

from lab.client import get_db
from lab.show import step, table, title

db = get_db()
employees = db.employees

title("05 - Consistencia")

step("Write concern: tiempo promedio de 100 actualizaciones con cada nivel")
rows = []
for label, concern in (("w=1 (solo PRIMARY)", WriteConcern(w=1)),
                       ("w=majority (2 de 3)", WriteConcern(w="majority")),
                       ("w=3 (todos)", WriteConcern(w=3, wtimeout=5000))):
    collection = employees.with_options(write_concern=concern)
    start = time.perf_counter()
    for i in range(100):
        collection.update_one({"employee_id": "E0002"}, {"$set": {"counter": i}})
    rows.append({"write concern": label, "ms por escritura": (time.perf_counter() - start) * 10})
table(rows)
print("Más nodos confirmando = más seguro y un poco más lento. 'majority' es el valor por defecto.")

step("w=4 en un replica set de 3 nodos: imposible de cumplir")
try:
    employees.with_options(write_concern=WriteConcern(w=4)).update_one({"employee_id": "E0002"}, {"$set": {"x": 1}})
except WriteConcernError as error:
    print("WriteConcernError:", error.details["codeName"])

step("Read preference: qué nodo atiende la lectura (20 lecturas con cada modo)")
for preference in (ReadPreference.PRIMARY, ReadPreference.SECONDARY, ReadPreference.NEAREST):
    served_by = {db.command("hello", read_preference=preference)["me"] for _ in range(20)}
    print(f"{preference.name:10} -> {sorted(served_by)}")
print("Leer de SECONDARY reparte la carga, pero puede devolver datos con un pequeño retraso.")

step("Read concern: 'local' (lo último del nodo) vs 'majority' (lo que ya tiene la mayoría y no se revertirá)")
for level in ("local", "majority"):
    doc = employees.with_options(read_concern=ReadConcern(level)).find_one({"employee_id": "E0002"}, {"counter": 1})
    print(f"{level:8} -> counter = {doc['counter']}")

step("Leer tus propias escrituras desde un SECONDARY: sesión con consistencia causal")
with db.client.start_session(causal_consistency=True) as session:
    employees.update_one({"employee_id": "E0002"}, {"$set": {"counter": 999}}, session=session)
    secondary = employees.with_options(read_preference=ReadPreference.SECONDARY,
                                       read_concern=ReadConcern("majority"))
    print("leído en un SECONDARY:", secondary.find_one({"employee_id": "E0002"}, {"_id": 0, "counter": 1},
                                                       session=session))
