#!/bin/bash
# Pre-startup account integrity check
# Verifies every game_users.accountId has a matching game_accounts entry.
# Creates placeholder entries for any orphans found.
# Run after MongoDB is up, before galaxybot-server starts.

DB_USER="${GALAXYBOT_DB_USER:-galaxybot}"
DB_PASS="${GALAXYBOT_DB_PASSWORD:-Hak4oYk44ZahfRrepkFc}"
DB_NAME="go2super"

MONGO="mongosh --quiet --username $DB_USER --password $DB_PASS --authenticationDatabase $DB_NAME $DB_NAME"

log() { echo "[check-accounts] $*"; }

log "Checking account integrity..."

missing=$($MONGO --eval '
const orphans = [];
db.game_users.find().forEach(function(u) {
  const aid = u.accountId;
  if (!aid) { orphans.push({user: u.username, reason: "null accountId"}); return; }
  const acc = db.game_accounts.findOne({_id: aid});
  if (!acc) { orphans.push({user: u.username, accountId: aid.toString(), reason: "missing account"}); }
});
print(JSON.stringify(orphans));
' 2>/dev/null)

count=$(echo "$missing" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null)

if [ "$count" = "0" ] || [ -z "$missing" ]; then
  log "All accounts OK — no orphans found."
  exit 0
fi

log "Found $count orphan(s). Creating placeholder accounts..."

echo "$missing" | python3 -c "
import sys, json, subprocess, bcrypt, re
orphans = json.load(sys.stdin)
for o in orphans:
    uname = o['user']
    aid = o.get('accountId', '')
    # generate $2a$ hash for test1234
    h = bcrypt.hashpw(b'test1234', bcrypt.gensalt(12)).decode()
    h = re.sub(r'^\$2[ab]\$', r'\$2a\$', h)
    email = uname.lower() + '@recovered.supergo2.com'
    js = f'''
var oid;
if (\"{aid}\") {{ oid = ObjectId(\"{aid}\"); }}
else {{ oid = new ObjectId(); }}
db.game_accounts.insertOne({{
  _id: oid,
  username: \"{uname}\",
  email: \"{email}\",
  password: \"{h}\",
  vip: 0,
  registerDate: new Date(),
  accountStatus: \"REGISTER\",
  userRank: \"USER\",
  _class: \"com.go2super.database.entity.Account\"
}});
db.game_users.updateOne(
  {{username: \"{uname}\"}},
  {{\\\$set: {{accountId: oid.str}}}}
);
print('Created account for ' + \"{uname}\");
'''
    subprocess.run([
      'mongosh', '--quiet',
      '--username', '$DB_USER',
      '--password', '$DB_PASS',
      '--authenticationDatabase', '$DB_NAME',
      '$DB_NAME',
      '--eval', js
    ], capture_output=True)
    print(f'  Recovered: {uname}')
" 2>&1 | while read line; do log "$line"; done

log "Account integrity check complete."
exit 0
