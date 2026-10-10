from pymongo import MongoClient

from lab.config import MONGO_DB, MONGO_URI


# MongoClient keeps a connection pool and monitors the replica set: create one per process and reuse it
def get_client(uri=MONGO_URI, **kwargs):
    return MongoClient(uri, appname="mongodb-replication", tz_aware=True, **kwargs)


def get_db(client=None):
    return (client or get_client())[MONGO_DB]
