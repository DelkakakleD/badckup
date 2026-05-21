#!/usr/bin/env python3
"""DB health checker — scan for orphans, missing fields, collisions.
Usage: ./db-health.py [--json] [--fix]
       --json   output JSON only (for API consumption)
       --fix    attempt auto-fix for found issues"""

import json, os, subprocess, sys

MONGO_URI = "mongodb://galaxybot:Hak4oYk44ZahfRrepkFc@127.0.0.1:27017/go2super"
FIX_SCRIPT = '''
    var user = db.game_users.findOne({_id: ObjectId("%s")});
    if (!user) { print("NOT_FOUND"); quit(); }
    var setFields = {};
    if (!user.game_tasks || !user.game_tasks.currentDaily) setFields["game_tasks.currentDaily"] = [];
    if (!user.game_tasks || !user.game_tasks.claimedDailyAwards) setFields["game_tasks.claimedDailyAwards"] = [];
    if (!user.game_ships || !user.game_ships.repair) setFields["game_ships.repair"] = [];
    if (!user.game_bionic_chips || !user.game_bionic_chips.phases) setFields["game_bionic_chips.phases"] = [1,0,0,0,0];
    if (!user.game_rewards || !user.game_rewards.until) setFields["game_rewards.until"] = new Date();
    if (!user.game_stats || !user.game_stats.iglStats) setFields["game_stats.iglStats"] = {claimed:false, entries:0, fleetIds:[], rank:0};
    if (!user.game_user_emails) setFields["game_user_emails"] = {userEmails: []};
    if (Object.keys(setFields).length > 0) { db.game_users.updateOne({_id: user._id}, {$set: setFields}); print("FIXED:"+Object.keys(setFields).join(",")); }
    else { print("OK"); }
'''

def run_mongo(script):
    r = subprocess.run(["mongosh", MONGO_URI, "--quiet", "--eval", script], capture_output=True, text=True, timeout=30, env={**os.environ, "HOME": "/root"})
    return r.stdout.strip()

def find_orphan_accounts():
    """Accounts with no matching user"""
    out = run_mongo('''
        var orphans = [];
        db.game_accounts.find().forEach(function(a) {
            var u = db.game_users.findOne({accountId: a._id.toString()});
            if (!u) orphans.push({accountId: a._id.toString(), username: a.username, email: a.email});
        });
        print(JSON.stringify(orphans));
    ''')
    return json.loads(out) if out else []

def find_orphan_users():
    """Users with no matching account"""
    out = run_mongo('''
        var orphans = [];
        db.game_users.find().forEach(function(u) {
            var a = db.game_accounts.findOne({_id: ObjectId(u.accountId)});
            if (!a) orphans.push({userId: NumberInt(u.userId.valueOf()), username: u.username, accountId: u.accountId});
        });
        print(JSON.stringify(orphans));
    ''')
    return json.loads(out) if out else []

def find_userid_collisions():
    out = run_mongo('''
        var dups = [];
        db.game_users.aggregate([{$group: {_id: "$userId", count: {$sum: 1}, users: {$push: {username: "$username", _id: "$_id"}}}}, {$match: {count: {$gt: 1}}}]).toArray().forEach(function(d) {
            dups.push({userId: NumberInt(d._id), count: d.count, users: d.users});
        });
        print(JSON.stringify(dups));
    ''')
    return json.loads(out) if out else []

def find_missing_fields():
    out = run_mongo('''
        var issues = [];
        db.game_users.find().forEach(function(u) {
            var missing = [];
            if (!u.game_tasks || !u.game_tasks.currentDaily) missing.push("game_tasks.currentDaily");
            if (!u.game_tasks || !u.game_tasks.claimedDailyAwards) missing.push("game_tasks.claimedDailyAwards");
            if (!u.game_ships || !u.game_ships.repair) missing.push("game_ships.repair");
            if (!u.game_bionic_chips || !u.game_bionic_chips.phases) missing.push("game_bionic_chips.phases");
            if (!u.game_rewards || !u.game_rewards.until) missing.push("game_rewards.until");
            if (!u.game_stats || !u.game_stats.iglStats) missing.push("game_stats.iglStats");
            if (!u.game_user_emails) missing.push("game_user_emails");
            if (missing.length > 0) issues.push({userId: NumberInt(u.userId.valueOf()), username: u.username, missing: missing});
        });
        print(JSON.stringify(issues));
    ''')
    return json.loads(out) if out else []

def fix_user(oid):
    r = run_mongo(FIX_SCRIPT % oid)
    return r

def run(fix=False, json_output=False):
    results = {}
    results["orphan_accounts"] = find_orphan_accounts()
    results["orphan_users"] = find_orphan_users()
    results["userid_collisions"] = find_userid_collisions()
    results["missing_fields"] = find_missing_fields()
    results["total_users"] = int(run_mongo("db.game_users.countDocuments()"))
    results["total_accounts"] = int(run_mongo("db.game_accounts.countDocuments()"))

    if fix:
        fixes = {"fixed": []}
        for u in results["missing_fields"]:
            r = fix_user(u["userId"])
            if r and r != "OK":
                fixes["fixed"].append({"userId": u["userId"], "username": u["username"], "fixed": r})
        results["fixes_applied"] = fixes

    if json_output:
        print(json.dumps(results, default=str))
    else:
        print("=== DB Health Report ===")
        print(f"Users: {results['total_users']}, Accounts: {results['total_accounts']}")
        print(f"Orphan accounts (no user): {len(results['orphan_accounts'])}")
        print(f"Orphan users (no account): {len(results['orphan_users'])}")
        print(f"UserId collisions: {len(results['userid_collisions'])}")
        print(f"Users with missing fields: {len(results['missing_fields'])}")
        if results.get("fixes_applied"):
            print(f"Auto-fixed: {len(results['fixes_applied']['fixed'])} users")
        if results["orphan_accounts"] or results["orphan_users"] or results["userid_collisions"] or results["missing_fields"]:
            print("\nIssues found! Run with --fix to auto-repair missing fields.")

    return results

if __name__ == "__main__":
    fix = "--fix" in sys.argv
    json_output = "--json" in sys.argv
    run(fix=fix, json_output=json_output)
