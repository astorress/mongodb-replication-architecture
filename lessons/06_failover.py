# Lección 06 - Failover: el PRIMARY deja de serlo y el replica set elige otro, sin detener la aplicación.
#
# Un hilo escribe sin parar mientras el programa obliga al PRIMARY a renunciar (replSetStepDown).
# Las retryable writes del driver reintentan una vez la escritura que coincide con la elección.
import threading
import time

from pymongo.errors import PyMongoError

from lab.client import get_client
from lab.config import MONGO_DB
from lab.show import step, table, title

client = get_client()
log = client[MONGO_DB].failover_log
log.drop()
stop = threading.Event()
ticks = []


def writer():
    second, ok, failed = int(time.time()), 0, 0
    while not stop.is_set():
        try:
            log.insert_one({"at": time.time()})
            ok += 1
        except PyMongoError:
            failed += 1
        now = int(time.time())
        if now != second:
            ticks.append({"second": len(ticks) + 1, "primary": client.primary and client.primary[0],
                          "writes_ok": ok, "writes_failed": failed})
            second, ok, failed = now, 0, 0
        time.sleep(0.01)


title("06 - Failover")

old_primary = client.admin.command("hello")["primary"]
step(f"PRIMARY actual: {old_primary}. Escribiendo continuamente durante 12 s...")
thread = threading.Thread(target=writer)
thread.start()
time.sleep(3)

step("Segundo 3: el PRIMARY renuncia y no puede volver a serlo durante 20 s")
client.admin.command("replSetStepDown", 20)
time.sleep(9)
stop.set()
thread.join()

table(ticks)
new_primary = client.admin.command("hello")["primary"]
print(f"\nPRIMARY antes: {old_primary} -> después: {new_primary}")
print(f"Escrituras fallidas: {sum(t['writes_failed'] for t in ticks)}. Con una renuncia ordenada la elección es casi")
print("inmediata y las retryable writes cubren el cambio. Si el PRIMARY se cae de golpe, los demás esperan ~10 s")
print("(electionTimeoutMillis) antes de votar, y las escrituras quedan en pausa ese tiempo.")
print(f"Documentos escritos: {log.count_documents({})}")
print("mongo1 tiene priority 2: en ~20 s volverá a ganar la elección.")
log.drop()

step("Prueba también apagando el contenedor del PRIMARY desde el host:")
print("  docker stop MongoNode1   # observa con: python lessons/04_replica_set.py")
print("  docker start MongoNode1")
