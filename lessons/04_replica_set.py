# Lección 04 - Anatomía del replica set: miembros, roles, oplog y cómo se copian los datos.
from pymongo import MongoClient

from lab.client import get_client
from lab.config import MONGO_DB
from lab.show import show, step, table, title

client = get_client()
admin = client.admin

title("04 - Replica set rs0")

step("hello: lo que el driver pregunta para descubrir la topología")
hello = admin.command("hello")
show({k: hello[k] for k in ("setName", "hosts", "primary", "me", "isWritablePrimary")})

step("replSetGetStatus: estado de cada miembro")
status = admin.command("replSetGetStatus")
primary_optime = next(m["optimeDate"] for m in status["members"] if m["stateStr"] == "PRIMARY")
table([{
    "member": m["name"],
    "state": m["stateStr"],
    "health": m["health"],
    "last_op": m["optimeDate"].strftime("%H:%M:%S"),
    "lag_s": (primary_optime - m["optimeDate"]).total_seconds(),
    "copies_from": m.get("syncSourceHost") or "-",
} for m in status["members"]])

step("replSetGetConfig: prioridad y votos de cada miembro")
config = admin.command("replSetGetConfig")["config"]
table([{"member": m["host"], "priority": m["priority"], "votes": m["votes"]} for m in config["members"]])
print("El de mayor prioridad es el preferido como PRIMARY. Con 3 votos, una elección necesita 2 (mayoría).")

step("Escribir en el PRIMARY y leer el mismo documento DIRECTAMENTE en cada nodo")
db = client[MONGO_DB]
db.employees.update_one({"employee_id": "E0001"}, {"$set": {"note": "replicado"}})
for host in hello["hosts"]:
    node = MongoClient(f"mongodb://{host}/?directConnection=true", tz_aware=True)
    doc = node[MONGO_DB].employees.find_one({"employee_id": "E0001"}, {"_id": 0, "note": 1})
    role = node.admin.command("hello")
    print(f"{host:14} {'PRIMARY' if role['isWritablePrimary'] else 'SECONDARY':10} -> {doc}")
    node.close()

step("oplog (local.oplog.rs): el registro de operaciones que los SECONDARY copian y aplican")
table(({"time": e["wall"].strftime("%H:%M:%S"), "op": e["op"], "ns": e["ns"],
        "change": str(e.get("o", {}))[:60]}
       for e in client.local["oplog.rs"].find({"ns": f"{MONGO_DB}.employees"}).sort("$natural", -1).limit(5)))
print("op: i = insert, u = update, d = delete")
first, last = (client.local["oplog.rs"].find_one(sort=[("$natural", d)])["wall"] for d in (1, -1))
print(f"El oplog cubre desde {first:%Y-%m-%d %H:%M} hasta {last:%Y-%m-%d %H:%M} (ventana de replicación)")
