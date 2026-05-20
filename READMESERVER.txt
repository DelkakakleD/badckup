# GalaxyBot Game Server - Codebase Analysis

## TABLE OF CONTENTS
1. [Architecture Overview](#architecture-overview)
2. [USERS - User Entity & Subsystems](#users)
3. [FLEETS - Fleet System](#fleets)
4. [CORPS/CONSORTIUMS - Corp Entity](#corpsconsortiums)
5. [RESEARCH/TECH - Tech Tree](#researchtech)
6. [ARENA/Battle - BattleService](#arenabattle)
7. [IGL - IGLService](#igl)
8. [LEAGUE - Rank & League System](#league)
9. [COMMUNICATION - PacketRouter & Packets](#communication)
10. [DATABASE - MongoDB Collections & Repositories](#database)

---

## Architecture Overview

### Request Flow
```
Client → GameServer (ServerSocket) → GameServerReceiver → PacketRouter.fireEvent()
       → PacketListener → Service Methods → Entity.save() → Cache → MongoDB
```

### Key Components
- **GameServer**: Implements `SmartServer`, handles TCP connections on port
- **PacketRouter**: Singleton, maps packet types to handler methods via reflection
- **Packet**: Base class for all client/server messages
- **Services**: Singleton instances handling business logic
- **Caches**: In-memory caches backed by MongoDB repositories

### Technology Stack
- **Framework**: Spring Boot
- **Database**: MongoDB (Morphia ODM)
- **Networking**: Apache MINA (IoBuffer), Custom SmartServer/SmartSession
- **Serialization**: Go2Buffer (custom little-endian buffer protocol)

---

## <a name="users"></a>USERS - User Entity & Subsystems

### Main Entity: User
**Location**: `com.go2super.database.entity.User`

#### Core Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | ObjectId | MongoDB ID |
| `accountId` | String | Account reference |
| `guid` | int | Global user ID |
| `userId` | long | Unique user identifier |
| `username` | String | Player name |
| `ground` | int | Ground unit count |
| `gMapId` | int | Current galaxy map |
| `consortiaId` | int | Corp ID |
| `consortiaJob` | int | User's corp job/role |
| `consortiaUnionLevel` | int | Corp union level |
| `gameServerId` | int | Server instance |
| `card1`, `card2`, `card3`, `cardUnion` | int | Card-related |
| `chargeFlag` | int | Payment status |
| `lotteryStatus` | int | Lottery state |
| `warScore` | int | War points |
| `leagueCount` | byte | League participation |
| `notDisturb` | boolean | Do not disturb mode |
| `lastRecruit`, `lastDayUpdate` | Date | Timers |
| `userMaxPpt` | double | Max power |

#### Sub-Entities (Embedded in User)
- **`flag`** → `UserFlag` (user flags/settings)
- **`stats`** → `UserStats` (level, exp, league stats, champ stats, igl stats)
- **`ships`** → `UserShips` (ship inventory)
- **`techs`** → `UserTechs` (research levels)
- **`tasks`** → `UserTasks` (daily tasks)
- **`territories`** → `UserTerritories` (conquered territories)
- **`chips`** → `UserChips` (bionic chips)
- **`rewards`** → `UserRewards` (rewards tracking)
- **`metrics`** → `UserMetrics` (game metrics)
- **`shipUpgrades`** → `UserShipUpgrades` (ship upgrade tree)
- **`resources`** → `UserResources` (gold, he3, metal, vouchers, etc.)
- **`buildings`** → `UserBuildings` (base building state)
- **`storage`** → `UserStorage` (warehouse storage)
- **`userEmailStorage`** → `UserEmailStorage` (inbox)
- **`inventory`** → `UserInventory` (items)
- **`corpInventory`** → `CorpInventory` (corp warehouse access)
- **`friends`** → `List<Integer>` (friend guids)
- **`blockUsers`** → `List<Integer>` (blocked guids)

### UserStats Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserStats`

| Field | Type |
|-------|------|
| `level` | int |
| `exp` | int |
| `restrictedUsedEntries` | int |
| `raidAttemptsEntries` | int |
| `raidInterceptEntries` | int |
| `instance` | int |
| `trial` | int |
| `sp` | int (skill points) |
| `kills` | int |
| `nextInvitation` | Date |
| `collectedPoints` | boolean |
| `buffs` | `List<UserBoost>` |
| `leagueStats` | `UserLeagueStats` |
| `champStats` | `UserChampStats` |
| `iglStats` | `UserIglStats` |

**Methods**:
- `addExp(int)` - Adds experience, handles level-up via `LevelsJson`
- `getMaxSp()` - Returns `20 + level`
- `hasTruce()` - Checks for PLANET_PROTECTION bonus

### UserResources Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserResources`

| Field | Type | Description |
|-------|------|-------------|
| `gold` | long | Currency (max 9999999999) |
| `he3` | long | Helium-3 fuel |
| `metal` | long | Metal ore |
| `vouchers` | long | Shop vouchers |
| `mallPoints` | long | Mall currency |
| `coupons` | long | Coupons |
| `corsairs` | long | Corsair tokens |
| `honor` | long | Honor points |
| `badge` | long | Badges |
| `championPoints` | long | Championship points |
| `freeSpins` | int | Free lottery spins |
| `lastSpin` | Date | Last spin time |

**Methods**:
- `refresh()` - Caps resources at MAX_RESOURCES (9999999999)

### UserTechs Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserTechs`

| Field | Type |
|-------|------|
| `techs` | `List<UserTech>` |
| `upgrade` | `TechUpgrade` |

**Methods**:
- `has(int techId)` / `has(String techName)` - Check if tech owned
- `has(int techId, int level)` / `has(String, int)` - Check minimum level
- `getLevel(int)` / `getLevel(String)` - Get tech level
- `getTech(String)` - Get specific tech

### UserService Key Methods
**Location**: `com.go2super.service.UserService`

- `onStartUp()` - Initializes boost timers on server start
- `updateResources(User)` - Refreshes user resources
- `updateStats(User)` - Updates user statistics
- `updateShips(User)` - Syncs ship data
- `updateEmails(User)` - Manages inbox (sorts, limits to 50)
- `getUserQueues(User)` - Returns `ResponseTimeQueuePacket` with active boosts

---

## <a name="fleets"></a>FLEETS - Fleet System

### Main Entity: Fleet
**Location**: `com.go2super.database.entity.Fleet`
**Implements**: `Serializable`

#### Core Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | ObjectId | MongoDB ID |
| `shipTeamId` | int | Ship team ID |
| `galaxyId` | int | Current galaxy |
| `guid` | int | Owner user GUID |
| `name` | String | Fleet name |
| `commanderId` | int | Commander leading fleet |
| `he3` | int | Fuel amount |
| `bodyId` | int | Fleet body/hull ID |
| `rangeType` | int | Movement range |
| `preferenceType` | int | Fleet preferences |
| `posX`, `posY` | int | Position coordinates |
| `direction` | int | Facing direction |
| `match` | boolean | In match flag |
| `additionalGrowth` | double | Growth bonus |
| `forceTechs` | boolean | Force tech flag |
| `fleetBody` | `ShipTeamBody` | Ship composition |
| `fleetMatch` | `FleetMatch` | Match data |
| `fleetTransmission` | `FleetTransmission` | Transmission state |
| `fleetInitiator` | `FleetInitiator` | Battle initiator |

#### Key Methods
- `remove()` - Deletes from FleetCache
- `save()` - Saves to FleetCache
- `getCommander()` - Gets Commander via CommanderService
- `bodyId()` - Gets best hull ID from fleet body
- `getMaxHe3()` - Calculates max fuel capacity
- `getSupply()` - Returns He3 consumption (ceil)
- `getHe3Consumption()` - Calculates total fuel usage
- `getTransmissionRate()` - Gets transmission rate (-1.0 if none)

### FleetMatch Sub-Entity
Contains matching data for battle pairing

### FleetTransmission Sub-Entity
Tracks fleet movement/transmission state

### FleetInitiator Sub-Entity
Tracks battle initiation data

### ShipTeamBody
**Location**: `com.go2super.obj.game.ShipTeamBody`
Contains `List<ShipTeamNum>` - ship cell composition

---

## <a name="corps"></a>CORPS/CONSORTIUMS - Corp Entity

### Main Entity: Corp
**Location**: `com.go2super.database.entity.Corp`

#### Core Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | ObjectId | MongoDB ID |
| `corpId` | int | Unique corp ID |
| `contribution` | int | Total corp contribution |
| `maxMembers` | int | Max member capacity (default 30) |
| `rbpLimit` | int | Resource building plan limit |
| `resourceBonus` | double | Resource bonus multiplier |
| `mergeBonus` | double | Merge bonus |
| `contributionMerge` | int | Merge contribution |
| `contributionMall` | int | Mall contribution |
| `wealth` | int | Corp treasury |
| `icon` | int | Corp icon ID |
| `name` | String | Corp name |
| `blocId` | ObjectId | Alliance/Bloc ID |
| `acronym` | String | Corp tag |
| `philosophy` | String | Corp description |
| `bulletin` | String | Corp bulletin board |
| `planets` | int | Owned planets |
| `territories` | int | Conquered territories |
| `level` | int | Corp level |
| `mallLevel` | int | Corp mall level |
| `mergingLevel` | int | Merge research level |
| `warehouseLevel` | int | Warehouse level |
| `fees` | int | Entry fees |
| `piratesLevel` | int | Pirates defense level |
| `lastPirates` | Date | Last pirates attack |
| `consortiaJobName` | `ConsortiaJobName` | Job titles |
| `history` | `CorpHistory` | Corp history |
| `members` | `CorpMembers` | Member list |
| `corpUpgrade` | `CorpUpgrade` | Upgrade tree |
| `corpTerritories` | `CorpTerritories` | Territory holdings |

#### CorpMember Sub-Entity
**Location**: `com.go2super.database.entity.sub.CorpMember`

| Field | Type |
|-------|------|
| `guid` | int |
| `contribution` | int |
| `job` | String |
| `level` | int |

#### CorpMembers Sub-Entity
Contains `List<CorpMember>` and `List<CorpMember>` (recruits)

### CorpService Key Methods
**Location**: `com.go2super.service.CorpService`

- `findRecruitsByPage(int page, int size, int corpId)` - Paginated recruit list
- `getCorpByUser(int guid)` - Get corp via CorpCache
- `createCorp(SmartString name, String philosophy, char acronym)` - Creates new corp
- `getCorpCache()` - Returns CorpCache

### Corp Job Names
Uses `ConsortiaJobName` with titles: Recruit, Colonel, Commandant, Captain, Soldier

---

## <a name="researchtech"></a>RESEARCH/TECH - Tech Tree

### UserTechs Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserTechs`

| Field | Type |
|-------|------|
| `techs` | `List<UserTech>` |
| `upgrade` | `TechUpgrade` |

### UserTech Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserTech`

| Field | Type |
|-------|------|
| `id` | int |
| `level` | int |

### TechUpgrade Sub-Entity
Manages ongoing tech upgrades

### Key Methods (UserTechs)
- `has(int techId)` - Returns boolean
- `has(String techName)` - Returns boolean
- `getLevel(int techId)` - Returns tech level
- `getTech(String techName)` - Returns UserTech object
- `getLevel(String techName)` - Returns level

### Tech System Notes
- Techs are stored as embedded documents in User
- Accessed via User.getTechs() → UserTechs
- Levels managed through upgrade system

---

## <a name="arenabattle"></a>ARENA/Battle - BattleService

### BattleService Overview
**Location**: `com.go2super.service.BattleService`
**Size**: ~88KB (largest service)

#### Fields
| Field | Type |
|-------|------|
| `battles` | `CopyOnWriteArrayList<GameBattle>` |
| `battleByRunnable` | `ConcurrentHashMap<Runnable, GameBattle>` |
| `battleByMatchId` | `ConcurrentHashMap<String, GameBattle>` |
| `instance` | static BattleService |

#### Key Methods
- `setup()` - Initializes battles, loads fleets from cache, cleans up NPC commanders
- `run(Match)` - Creates MatchRunnable based on match type (ArenaMatch/ChampMatch)
- `run(MatchRunnable, boolean)` - Creates Thread, registers battle
- `isRunning(Match)` - Checks if match is active
- `getBattles(int guid)` - Gets battles by user GUID
- `getBattle(String matchId)` - Gets battle by match ID

### Match Types
**Location**: `com.go2super.service.battle.match.*`

| Class | Description |
|-------|-------------|
| `ArenaMatch` | Arena battles |
| `ChampMatch` | Championship battles |
| `LeagueMatch` | League battles |
| `WarMatch` | War battles |
| `IglMatch` | IGL racing battles |
| `InstanceMatch` | PvE instance battles |
| `RaidMatch` | Raid battles |

### Match Classes
**Location**: `com.go2super.service.battle.Match`

| Field | Type |
|-------|------|
| `matchType` | `MatchType` enum |
| `id` | String |
| `attackerFleetId` | int |
| `defenderFleetId` | int |
| `attackerGuid` | int |
| `defenderGuid` | int |

### GameBattle Classes
**Location**: `com.go2super.service.battle.GameBattle`

Builder pattern for constructing battles with Thread and MatchRunnable.

### MatchRunnable Classes
**Location**: `com.go2super.service.battle.MatchRunnable`

Contains:
- `Match match` - The match data
- `AreaEffect` - Area effect types and builder
- `AreaEffectType` enum

### Battle Sub-Entities
| Class | Description |
|-------|-------------|
| `BattleFleet` | Fleet in battle |
| `BattleFleetCell` | Cell in fleet formation |
| `BattleFleetTeam` | Team composition |
| `BattleAction` | Battle actions |
| `BattleCommander` | Commander in battle |
| `BattleEffect` | Active effects |
| `BattleElement` | Battle elements |
| `BattleFort` | Fortifications |
| `BattleMetadata` | Battle metadata |
| `BattleReport` | Battle report |
| `BattleRound` | Battle round |
| `BattleShipCache` | Ship cache |
| `BattleStructure` | Structures |
| `BattleTag` | Battle tags |
| `Pathfinder` | Pathfinding for battles |

---

## <a name="igl"></a>IGL - IGLService

### IGLPlayer Entity
**Location**: `com.go2super.database.entity.IGLPlayer`

| Field | Type |
|-------|------|
| `id` | ObjectId |
| `userId` | long |
| `fleetIds` | `List<Integer>` |

### IGLService Key Methods
**Location**: `com.go2super.service.IGLService`

| Field | Type |
|-------|------|
| `instance` | static IGLService |
| `iglPlayerRepository` | IGLPlayerRepository |
| `userToFleetIds` | `ConcurrentHashMap<Long, List<Integer>>` |
| `userToReport` | `ConcurrentHashMap<Long, LinkedList<RacingReportInfo>>` |
| `rankList` | `List<RacingRank>` |
| `enabled` | AtomicBoolean |

**Methods**:
- `setup()` - Loads all IGL players, builds rank list by user stats
- `addFleetIds(long userId, IntegerArray fleetIds)` - Adds fleets to player

### IGL Sub-Stats (UserIglStats)
**Location**: `com.go2super.database.entity.sub.UserIglStats`

| Field | Type |
|-------|------|
| `rank` | int |
| `entries` | int |

---

## <a name="league"></a>LEAGUE - Rank & League System

### LeagueRankService
**Location**: `com.go2super.service.league.LeagueRankService`

| Field | Type |
|-------|------|
| `instance` | static LeagueRankService |
| `MAX_RANK` | static final int |
| `cachedLeagueRank` | `List<List<UserLeagueLeaderboard>>` (10 leagues) |
| `cachedUser` | `Map<Integer, UserLeagueLeaderboard>` |
| `leaguesJson` | LeaguesJson |
| `userCache` | UserCache |

**Methods**:
- `setup()` - Clears caches, loads all users, builds 10 league leaderboards
- `update(User)` - Updates user league leaderboard entry
- `sortLeagueRank(int league)` - Sorts league by wins/losses/draws

### LeagueMatchService
Handles league match creation and management

### LeagueTime
Time-based league management

### UserLeagueStats Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserLeagueStats`

| Field | Type |
|-------|------|
| `wins` | int |
| `losses` | int |
| `draws` | int |
| `league` | int |

### UserChampStats Sub-Entity
**Location**: `com.go2super.database.entity.sub.UserChampStats`

Tracks championship statistics

---

## <a name="communication"></a>COMMUNICATION - PacketRouter & Packets

### PacketRouter
**Location**: `com.go2super.packet.PacketRouter`

#### Fields
| Field | Type |
|-------|------|
| `instance` | static PacketRouter (singleton) |
| `smartListeners` | `LinkedList<SmartListener>` |
| `packetsMap` | `Map<Integer, Class<? extends Packet>>` |

#### Key Methods
- `containsPacket(int type)` - Checks if packet type registered
- `broadcast(Packet, User...)` - Sends packet to all logged users except specified
- `fireEvent(Packet)` - Routes packet to listeners (reflection-based)
- `craftPackets()` - Uses Reflections to scan `com.go2super.packet` for subtypes
- `craftListeners()` - Registers all SmartListeners

### Packet Base Class
**Location**: `com.go2super.packet.Packet`

| Field | Type |
|-------|------|
| `blacklist` | `List<String>` (static, fields to skip) |
| `size` | int |
| `smartServer` | SmartServer |
| `socket` | Socket |
| `creationTime` | long |
| `responseTime` | long |
| `millis` | long |

**Key Methods**:
- `map(int, int, Go2Buffer, Socket, SmartServer)` - Deserializes packet from buffer

### Packet Flow
1. `GameServer` accepts socket connection
2. `GameServerReceiver` reads from `LittleEndianDataInputStream`
3. Calls `PacketRouter.fireEvent(packet)`
4. Reflection finds matching `SmartListener`
5. `PacketListener.onPacket(Packet)` handles the request
6. Response sent via `SmartServer.send(Packet)`

### SmartListener/PacketListener Pattern
- `SmartListener` binds `PacketClass` + `Method` + `Instance`
- `PacketListener` is the interface for handling packets

### Packet Types Available
| Class | Purpose |
|-------|---------|
| `Packet` | Base abstract class |
| `PacketHeartbeat` | Keepalive |
| `RequestKeepAlivePacket` | Client keepalive request |
| `PacketProcessor` | Request processing |
| `PacketRouter` | Routes packets |
| `PacketListener` | Interface for listeners |
| `DispatchType` | Dispatch enumeration |

---

## <a name="database"></a>DATABASE - MongoDB Collections & Repositories

### MongoDB Integration
- **ODM**: Morphia (MongoDB Java ODM)
- **ID Type**: `org.bson.types.ObjectId`

### Entity Relationship to Collections
| Entity | Collection |
|--------|------------|
| User | users |
| Fleet | fleets |
| Corp | corps |
| Commander | commanders |
| IGLPlayer | igl_players |
| Account | accounts |
| Bloc | blocs |
| Planet | planets |

### Repositories
**Location**: `com.go2super.database.repository.*`

| Repository | Methods |
|------------|---------|
| `UserRepository` | findByGuid, findByUserId, findAll |
| `FleetRepository` | findByGuid, findByGalaxyId, findAll |
| `CorpRepository` | findByCorpId, findByName, findAll |
| `CommanderRepository` | findByCommanderId, getNPCCommanders |
| `IGLPlayerRepository` | findByUserId, findAll |
| `AccountRepository` | findByAccountId |
| `BlocRepository` | findAll |
| `PlanetRepository` | findByGalaxyId, findResourcePlanets |
| `ShipModelRepository` | findAll |
| `GameBoostRepository` | findByPropId |
| `AutoIncrementRepository` | Next IDs for entities |
| `SanctionRepository` | findByGuid, findActive |
| `TradeRepository` | findActive |
| `StoreEventRepository` | findActive |
| `TeamModelsRepository` | findAll |
| `RiskIncidentRepository` | findActive |

### Caches
**Location**: `com.go2super.database.cache.*`

Caches provide in-memory access backed by repositories:
- `UserCache` - User entities
- `FleetCache` - Fleet entities
- `CorpCache` - Corp entities
- `CommanderCache` - Commander entities
- `PlanetCache` - Galaxy planets
- `ShipModelCache` - Ship definitions
- `AccountCache` - Account data
- `CorpCache` - Corp data
- `SanctionCache` - Active sanctions
- `TradeCache` - Active trades
- `StoreEventCache` - Active events
- `AutoIncrementCache` - ID generation
- `DashboardAccountCache` - Dashboard accounts

### Cache Pattern
```java
entity.save() → Service → Cache.save() → Repository.save()
```

---

## Additional Services

### UserService
**Location**: `com.go2super.service.UserService`

- Singleton pattern
- Manages user resources, stats, ships, emails, tasks
- Handles boost/buff management

### LoginService
**Location**: `com.go2super.service.LoginService`

- User authentication
- `LoggedGameUser` model for logged-in sessions
- `LoggedSessionUser` for session data

### ChatService
**Location**: `com.go2super.service.ChatService`

- Handles in-game chat

### GalaxyService
**Location**: `com.go2super.service.GalaxyService`

- Galaxy map management
- Planet cache access

### CommanderService
**Location**: `com.go2super.service.CommanderService`

- Commander CRUD operations
- `getCommander(int commanderId)` lookup
- CommanderCache access

### PacketService
**Location**: `com.go2super.service.PacketService`

- Packet-related utilities
- `getFleetCache()`, `getShipModel(int id)`

### AutoIncrementService
**Location**: `com.go2super.service.AutoIncrementService`

- `getNextCorpId()`, `getNextUserId()`, etc.

### JobService
**Location**: `com.go2super.service.JobService`

- Background job processing

### CLIEventService
Handles CLI events

### DashboardService/DashboardLoginService
Admin dashboard services

### DiscordService
Discord webhook integration

### MetricService
Game metrics collection

### ResourcesService
Global resources management

### ApiRateLimiter/LoginRateLimiter
Rate limiting for API/login endpoints

---

## Sub-Entity Summary

### User Sub-Entities (Embedded in User document)
| Class | Purpose |
|-------|---------|
| `UserFlag` | User flags |
| `UserStats` | Stats, buffs, league/champ/igl stats |
| `UserShips` | Ship inventory |
| `UserTechs` | Tech levels |
| `UserTasks` | Daily tasks |
| `UserTerritories` | Conquered territories |
| `UserChips` | Bionic chips |
| `UserRewards` | Rewards |
| `UserMetrics` | Metrics |
| `UserShipUpgrades` | Ship upgrades |
| `UserResources` | Resources (gold, he3, metal, etc.) |
| `UserBuildings` | Base buildings |
| `UserStorage` | Warehouse |
| `UserEmailStorage` | Inbox |
| `UserInventory` | Items |
| `CorpInventory` | Corp warehouse |
| `UserIPInfo` | IP tracking |
| `UserBoost` | Active boosts |

### Corp Sub-Entities
| Class | Purpose |
|-------|---------|
| `CorpHistory` | Corp history log |
| `CorpMembers` | Member list and recruits |
| `CorpUpgrade` | Corp upgrade tree |
| `CorpTerritories` | Corp territories |
| `CorpMember` | Individual member |
| `CorpInventory` | Corp warehouse |
| `CorpIncident` | Corp incidents |
| `RBPBuilding` | Resource building plan building |
| `RBPBuildings` | RBP building collection |

### Fleet Sub-Entities
| Class | Purpose |
|-------|---------|
| `FleetMatch` | Match data |
| `FleetTransmission` | Transmission state |
| `FleetInitiator` | Battle initiator |

### Commander Sub-Entities
| Class | Purpose |
|-------|---------|
| `BionicChip` | Bionic chip |
| `CommanderExpertise` | Expertise levels |
| `CommanderTrigger` | Commander triggers |

### Battle Sub-Entities
| Class | Purpose |
|-------|---------|
| `BattleAction` | Battle action |
| `BattleCommander` | Commander in battle |
| `BattleEffect` | Active effect |
| `BattleElement` | Battle element |
| `BattleFleet` | Battle fleet |
| `BattleFort` | Fortification |
| `BattleMetadata` | Metadata |
| `BattleReport` | Report |
| `BattleRound` | Round |
| `BattleShipCache` | Ship cache |
| `BattleStructure` | Structure |
| `BattleTag` | Tag |
| `BruiseShip` | Damaged ship |
| `FactoryShip` | Factory ship |
| `ShipUpgrade` | Ship upgrade |
| `TechUpgrade` | Tech upgrade |
| `TradeItem` | Trade item |
| `TradeShip` | Trade ship |
| `UserBuilding` | Building |
| `UserSameIPIncidentInfo` | Same IP incident |
| `TemporalSanction` | Temporal sanction |

### Email Sub-Entities
| Class | Purpose |
|-------|---------|
| `Email` | Email message |
| `EmailGood` | Email attachment |

### Discord Sub-Entities
| Class | Purpose |
|-------|---------|
| `DiscordHook` | Discord webhook |

### Event Sub-Entities
| Class | Purpose |
|-------|---------|
| `BadGuidIncident` | Bad GUID incident |
| `PacketFloodIncident` | Packet flood incident |
| `SameIPIncident` | Same IP incident |
| `StoreEventEntry` | Store event |

---

## Model Classes

### LoggedGameUser
**Location**: `com.go2super.obj.model.LoggedGameUser`

Holds logged-in user's session with SmartServer reference for sending packets.

### LoggedSessionUser/LoggedSessionAccount
Session data models.

### UserLeagueLeaderboard
**Location**: `com.go2super.obj.game.UserLeagueLeaderboard`

| Field | Type |
|-------|------|
| `guid` | int |
| `wins` | int |
| `losses` | int |
| `draws` | int |
| `league` | int |

### ConsortiaJobName
Job title definitions for corp members.

### ShipTeamBody/ShipTeamNum
Fleet ship composition.

### RacingReportInfo
IGL racing report info.

### TimeQueue
Queue management for boosts.

---

## Enum Types

### MatchType
Values: ARENA, CHAMP, LEAGUE, WAR, IGL, INSTANCE, RAID

### BonusType
Various bonus types including PLANET_PROTECTION

---

## Key Observations

### Singleton Pattern
All services use static `instance` field + `getInstance()` pattern.

### Cache-Aside Pattern
```
Read: Cache.get() → Repository.find() if miss
Write: Entity.save() → Cache.save() → Repository.save()
```

### Packet Reflection
`PacketRouter.craftPackets()` uses `org.reflections` to scan all Packet subclasses, enabling automatic routing without explicit registration.

### Battle System
- Largest service (88KB)
- Runs battles in separate Threads
- Tracks `GameBattle` with `MatchRunnable`
- Multiple match types for different game modes

### Resource Caps
- UserResources capped at 9,999,999,999 (MAX_RESOURCES)
- Level-based SP formula: `20 + level`

### Experience System
- Uses `LevelsJson` for level thresholds
- `addExp(int)` handles multi-level advancement

---

## File Locations Reference

| Component | Path |
|-----------|------|
| Entities | `BOOT-INF/classes/com/go2super/database/entity/` |
| Sub-Entities | `BOOT-INF/classes/com/go2super/database/entity/sub/` |
| Services | `BOOT-INF/classes/com/go2super/service/` |
| Battle Services | `BOOT-INF/classes/com/go2super/service/battle/` |
| Battle Matches | `BOOT-INF/classes/com/go2super/service/battle/match/` |
| League Services | `BOOT-INF/classes/com/go2super/service/league/` |
| Repositories | `BOOT-INF/classes/com/go2super/database/repository/` |
| Caches | `BOOT-INF/classes/com/go2super/database/cache/` |
| Packets | `BOOT-INF/classes/com/go2super/packet/` |
| Models | `BOOT-INF/classes/com/go2super/obj/model/` |
| Game Objects | `BOOT-INF/classes/com/go2super/obj/game/` |
| Resources | `BOOT-INF/classes/com/go2super/resources/` |
---

## Recent Bug Fixes (2026-05-19)

### 1. Battle Completion Fix (Commit 4fca826)
**Issue**: Battles completing but fleets stuck in match state, no mail/rewards sent.

**Root Cause**: `BattleService.stopMatch(Match, StopCause)` was only removing the GameBattle from internal tracking but NEVER calling `match.stop(stopCause)` to trigger cleanup.

**Fix**: Added `match.stop(stopCause)` call at start of `BattleService.stopMatch()`.

**Files Changed**:
- `GO2Server/src/main/java/com/go2super/service/BattleService.java` (line 488)

**Before**:
```java
public void stopMatch(Match match, StopCause stopCause) {
    GameBattle gameBattle = battleByMatchId.remove(match.getId());
    // ... only cleanup, no match.stop() called!
}
```

**After**:
```java
public void stopMatch(Match match, StopCause stopCause) {
    if (match != null) {
        match.stop(stopCause);  // Now properly cleans up!
    }
    GameBattle gameBattle = battleByMatchId.remove(match != null ? match.getId() : null);
    // ...
}
```

**Affected Match Types**: League, IGL, Raid, War, Arena, Champ, Instance

---

### 2. Account Creation Uniqueness Fix (Commit 3646e64)
**Issue**: Duplicate guid/userId causing account corruption, data conflicts.

**Root Cause**: `DashboardService` was using `RandomUtil.getRandomInt()` for guid instead of `AutoIncrementService`, and only checking guid uniqueness (not userId).

**Fix**: 
- Both `AccountService` and `DashboardService` now use `AutoIncrementService` for both guid and userId
- Added collision detection with 100-retry limit for each field
- Proper error messages returned if uniqueness cannot be achieved

**Files Changed**:
- `GO2Server/src/main/java/com/go2super/service/AccountService.java` (lines ~236-330)
- `GO2Server/src/main/java/com/go2super/service/DashboardService.java` (lines ~153-260)

**Before**:
```java
.guid(AutoIncrementService.getInstance().getNextGuid())
.userId(userId)
// ...
while (userCache.findByGuid(newUser.getGuid()) != null) {
    newUser.setGuid(RandomUtil.getRandomInt(MAX_PLANET));  // Wrong!
}
```

**After**:
```java
.userId(userId)
// ...
int maxRetries = 100;
int retryCount = 0;
while (userCache.findByGuid(newUser.getGuid()) != null) {
    if (++retryCount >= maxRetries) {
        return BasicResponse.builder().code(500).message("GUID_GENERATION_FAILED").build();
    }
    newUser.setGuid(AutoIncrementService.getInstance().getNextGuid());
}
// Also checks userId uniqueness similarly
```

---

### 3. PlayerListener Null Check Fix (Commit 4fca826)
**Issue**: NullPointerException when user.getPlanet() returns null.

**Fix**: Added null check before using userPlanet in PlayerListener.

---

## Git Commits Summary

| Commit | Description |
|--------|-------------|
| `4fca826` | BattleService fix: stopMatch now calls match.stop() before cleanup |
| `3646e64` | Add uniqueness checks for guid and userId on account creation |

---

## Current Server State

- **JAR**: `/home/kali/Desktop/SRVRINSTALL/game-server-0.8.1.jar` (62.7MB, built May 19 07:11)
- **Running**: Yes (ports 9090, 5150, 90, 9091 active)
- **MongoDB**: Connected (galaxybot:Hak4oYk44ZahfRrepkFc@127.0.0.1:27017/go2super)
- **Git**: Pushed to origin/master

---

## Key File Paths

| Purpose | Path |
|---------|------|
| Server Source | `/home/kali/Desktop/GalaxyBot-master/GO2Server/src/main/java/` |
| Build Output | `/home/kali/Desktop/GalaxyBot-master/GO2Server/target/game-server-0.8.1.jar` |
| Deploy Folder | `/home/kali/Desktop/SRVRINSTALL/` |
| Client Decompiled | `/tmp/swfs_decompiled/` |
| Server Decompiled | `/tmp/server_decompiled/` |

