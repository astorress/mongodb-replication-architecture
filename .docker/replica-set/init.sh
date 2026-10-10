#!/bin/bash
set -e

echo "Initiating replica set rs0"
mongosh "mongodb://mongo1:27017/?directConnection=true" --quiet --eval "
  try {
    rs.status();
    print('  already initiated');
  } catch (e) {
    if (e.codeName !== 'NotYetInitialized') throw e;
    rs.initiate({
      _id: 'rs0',
      members: [
        { _id: 0, host: 'mongo1:27017', priority: 2 },
        { _id: 1, host: 'mongo2:27017', priority: 1 },
        { _id: 2, host: 'mongo3:27017', priority: 1 }
      ]
    });
  }"

echo "Waiting for a PRIMARY"
until mongosh "mongodb://mongo1:27017/?directConnection=true" --quiet \
  --eval "rs.status().members.some(m => m.stateStr === 'PRIMARY')" 2>/dev/null | grep -q true; do
  sleep 1
done

mongosh "mongodb://mongo1:27017/?directConnection=true" --quiet \
  --eval "rs.status().members.forEach(m => print('  ' + m.name + ' -> ' + m.stateStr))"
echo "Replica set ready"
