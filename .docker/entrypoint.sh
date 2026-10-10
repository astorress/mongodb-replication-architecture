#!/bin/bash

COLOR_GREEN=$(tput setaf 2)
COLOR_BLUE=$(tput setaf 4)
COLOR_MAGENTA=$(tput setaf 5)
COLOR_DEFAULT=$(tput sgr0)

EXEC_PATH=$(dirname $(readlink -f "$0"))
HOME_PATH=$EXEC_PATH/..
SRC_PATH=$HOME_PATH/src
PYTHON_DIST_PACKAGES_PATH=/usr/local/lib/python3.13/site-packages
STEP=1
STEP_COUNT=3

# Generate home path file and add it to Python search path
echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Generating ${COLOR_BLUE}mongodb-replication.pth${COLOR_GREEN} file and adding it to Python search path.${COLOR_DEFAULT}"
echo "$(readlink -f $SRC_PATH)" | sudo tee $PYTHON_DIST_PACKAGES_PATH/mongodb-replication.pth
let STEP++

# Install Python requirements.txt once. If requirements are satisfied, installation is skipped
pip freeze | sort > /tmp/installed.txt
sed -E 's/#.*//; s/^[[:space:]]+//; s/[[:space:]]+$//' "$HOME_PATH/requirements.txt" \
  | sed '/^$/d' \
  | sort > /tmp/required.txt
MISSING_LINES=$(comm -23 /tmp/required.txt /tmp/installed.txt | wc -l)
if [ "$MISSING_LINES" -eq 0 ]; then
  echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Python requirements already satisfied. Skipping installation.${COLOR_DEFAULT}"
else
  echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Installing Python requirements.txt dependencies...${COLOR_DEFAULT}"
  sudo pip install --upgrade --upgrade-strategy only-if-needed -r "$HOME_PATH/requirements.txt"
fi
rm /tmp/installed.txt /tmp/required.txt
let STEP++

# Wait until the replica set has a PRIMARY
echo "${COLOR_MAGENTA}${STEP}/$STEP_COUNT:${COLOR_GREEN} Waiting for the replica set at ${COLOR_BLUE}$MONGO_URI${COLOR_GREEN}...${COLOR_DEFAULT}"
until mongosh "$MONGO_URI" --quiet --eval "db.hello().primary" 2>/dev/null | grep -q mongo; do
  sleep 2
done
mongosh "$MONGO_URI" --quiet --eval "rs.status().members.forEach(m => print('  ' + m.name + ' -> ' + m.stateStr))"

echo "${COLOR_GREEN}Ready. Next step: ${COLOR_BLUE}python lessons/00_seed.py${COLOR_DEFAULT}"
