# GalaxyBot Server — Project Context

## Server Architecture
- **Game server**: Java 21 Spring Boot fat JAR at `/opt/galaxybot/game-server-patched.jar`
- **WebSocket bridge**: Python 3 at `/opt/galaxybot/ws-bridge.py` (port 9091, relays WS→TCP)
- **Admin service**: Python 3 at `/opt/galaxybot/admin-register.py` (port 9191, account creation API)
- **MongoDB**: 8.0, database `go2super`, auth user `galaxybot`
- **OS**: Debian 13 (trixie), kernel 6.12

## Ports
- `9090` — HTTP REST API + Dashboard
- `9091` — WebSocket bridge (game client → raw TCP)
- `843` — Flash crossdomain policy
- `5150` — Game login socket (raw TCP)
- `90` — Game world socket (raw TCP)
- `27017` — MongoDB
- `9191` — Admin account creation service

## Services (all systemd)
- `galaxybot-server` — Java game server
- `galaxybot-mongod` — MongoDB (Type=forking workaround for kernel compat)
- `galaxybot-wsbridge` — WebSocket bridge
- `galaxybot-admin` — Account creation API

## API Endpoint Quirks
LoginController has class-level `@RequestMapping("${application.services.login}")` = `/login`, and method-level `@PostMapping("/login/account")`. Effective paths:
- **Login**: `POST /login/login/account`
- **Register**: `POST /login/register/account`
- **Create character**: `POST /account/create/user` (requires auth token from login)

## Account Creation (Working Method)
The single-step endpoint at `POST /admin/create` (port 9191) does:
1. Register account → Login → Create character
2. Fix missing MongoDB fields: `currentDaily`, `repair`, `phases`, `iglStats`, etc.
3. Detect & resolve userId collisions
4. Restart server

TUI: `python3 /opt/galaxybot/create-account.py`
Web form: `http://<server>:9191/`

## Known Bugs
1. **createUser() missing fields** — `game_tasks.currentDaily`, `game_ships.repair`, `game_tasks.claimedDailyAwards`, `game_bionic_chips.phases`, `game_rewards.until`, `game_stats.iglStats` not initialized. Must set after creation via MongoDB.
2. **auto_increment collection empty** — counters reset on restart, causing userId collisions. Finalize script handles this.
3. **Dashboard register tab broken** — `_api()` helper overrides Authorization with admin token. Use port 9191 instead.
4. **Welcome email items** — prop IDs 1572, 905, 906, 907 missing client icons (grey blocks). Located in `AccountService.createWelcomeEmail()` — calls `email.addGood(id, qty)`.
5. **userId stored as wrong BSON type** — NumberLong arithmetic in JavaScript does string concat. Finalize script uses NumberInt now.
6. **Git push to GitHub fails** — remote diverged. Needs `git pull --rebase`.

## Config Files
- `SRVRINSTALL/install.sh` — Full server installer
- `SRVRINSTALL/start.sh` / `stop.sh` — Service lifecycle
- `SRVRINSTALL/healthcheck.sh` — Health check script
- `SRVRINSTALL/backup-full.sh` — Daily full backup (3am, 7-day retention)
- `SRVRINSTALL/backup-hourly.sh` — Hourly git + mongodump
- `SRVRINSTALL/backup-mongodb.sh` — MongoDB-only backup
- `SRVRINSTALL/admin-register.py` — Account creation API (port 9191)
- `SRVRINSTALL/create-account.py` — TUI account creator
- `SRVRINSTALL/mongod.conf` — MongoDB config (3GB WiredTiger cache)
- `SRVRINSTALL/99-galaxybot.conf` — sysctl tuning (swappiness=10)
- `SRVRINSTALL/USERCREATION.txt` — Step-by-step account creation guide
- `SRVRINSTALL/operations.log` — Full operations log

## Restore Points
- `/opt/galaxybot/restore-points/galaxybot-restore-20260519-201305.tar.gz` (164MB)
- Restore script: `/opt/galaxybot/restore-points/restore.sh`
- Contains: MongoDB dump, systemd services, SRVRINSTALL files, JAR, Python scripts, configs, logs

## Dashboard
- URL: `http://<server>:9090/dashboard.html`
- Admin login: `admin@supergo2.com` / `Ff5E!68a*5on` (overridable via `GALAXYBOT_ADMIN_PASSWORD`)
- Tabs: Overview, Players, Accounts, Game Accounts, Player, Bans, Admin, Config, Restart, Resources, Commands, Logs, Champs, Gift, Register

## MongoDB Collections (go2super)
- `game_accounts` — login accounts (username, email, password, rank)
- `game_users` — characters (userId, guid, ground, sub-objects)
- `game_planets` — USER_PLANET + HUMAROID_PLANET + RESOURCES_PLANET
- `game_auto_increments` — (EMPTY — counters not persisted)
- `game_models` — ship models (175 entries)
- `game_account_sessions` — login sessions
- `game_dashboard_accounts` — admin dashboard accounts

## Ground/Planet Type Mapping (character creation)
Client sends `ground` value → stored value:
- `ground: 1` → stored as `2` (green planet)
- `ground: 2` → stored as `0` (desert planet)  
- `ground: 3` → stored as `1` (ice planet)

## MAX_PLANET Constant
Hardcoded in `AccountService` as `8388607`. Used as ceiling for random GUID generation on collision.

## Password Hashing
- Must use bcrypt with `$2a$` prefix (NOT `$2b$`) — Spring Security in the JAR only accepts `$2a$`
- Legacy Jasypt passwords auto-migrated to bcrypt on successful login

## Bytecode Patches (JAR)
The `game-server-patched.jar` has byte-level patches:
- `LoginService.class` — IP rate limit bypass (registration limit check disabled)
- `LoginRateLimiter` / `ApiRateLimiter` — rate limit bypass patches (return-false→return-true)

## Server IP
Configured via `SERVER_IP` env var in service file. Current: `77.68.25.39`
Set in `/etc/systemd/system/galaxybot-server.service`: `Environment=SERVER_IP=77.68.25.39`

## Welcome Email Items (AccountService.createWelcomeEmail)
```
addGood(1572, 1)   — commanderChest (GREY BLOCK — no client icon)
addGood(905, 6)    — buff:metalMiningBoost (GREY BLOCK)
addGood(906, 6)    — buff:he3MiningBoost (GREY BLOCK)
addGood(907, 6)    — buff:goldProductionBoost (GREY BLOCK)
addGood(923, 5)    — galaxyTransfer (works)
addGood(921, 1000) — loudspeaker (works)
addGood(924, 10)   — resettingCard (works)
addGood(925, 4)    — mergeChip (works)
addGood(937, 1)    — advTruceCard (works)
addGood(1119, 20)  — rawGemstones (works)
```
Items 1572, 905, 906, 907 exist in server props data but client SWF lacks their icons. Replace with 924, 925, 1119 for visible items.

## Rebuilding the JAR
```bash
JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 ./mvnw clean package -DskipTests
```
Outputs to `target/game-server-0.8.1.jar`. Must be Java 21 (Java 25 default on Kali breaks Spring Boot).

## User/Account Document Structure (for manual MongoDB fixes)
**game_accounts**: `{_id, username, email, password, vip, banUntil, accountStatus, userRank, registerDate}`
**game_users**: `{_id, accountId, guid, userId, username, ground, gMapId, consortiaId, gameServerId, game_stats, game_ships, game_user_techs, game_tasks, game_territories, game_bionic_chips, game_rewards, game_metrics, game_upgrades, game_resources, game_buildings, game_resource_storage, game_user_emails, game_user_inventory, game_user_friends}`
**game_planets (USER_PLANET)**: `{_id, userObjectId, userId, starFace, untilFlag, type: "USER_PLANET", position: {x, y}}`

## Quick Fixes
- Missing fields on existing user: `db.game_users.updateOne({username: "X"}, {$set: {"game_tasks.currentDaily": [], "game_ships.repair": [], "game_tasks.claimedDailyAwards": [], "game_bionic_chips.phases": [1,0,0,0,0], "game_rewards.until": new Date(), "game_stats.iglStats": {claimed:false, entries:0, fleetIds:[], rank:0}}})`
- Fix planet userId type: `db.game_planets.updateOne({userObjectId: "<user._id>"}, {$set: {userId: NumberInt(<newId>)}})`
