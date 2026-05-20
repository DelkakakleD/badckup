MongoDB Schema Reference (GalaxyBot go2super)
================================================

COLLECTIONS
-----------
game_accounts          - auth/account level (8 docs)
game_users             - player entity (5 docs)
game_planets           - all planets (2944 docs: 3 user, 210 resources, 2731 humaroid)
game_dashboard_accounts - dashboard admin (1 doc)
game_dashboard_account_sessions - dashboard sessions (116 docs)
game_account_sessions  - game sessions (5 docs)
game_users_ips          - IP tracking (6 docs)
game_risk_incidents     - risk/fraud log (2 docs)
game_corps              - corps/clans (1 doc)
game_team_models        - fleet/ship templates (2 docs)
game_fleets             - active fleets (31 docs)
game_commanders         - commander cards (7 docs)
game_models             - ship/item models (184 docs)
game_boosts             - buffs/boosts (16 docs)
game_trades             - auction/trade listings (1 doc)
game_store_events       - store event state (1 doc)
game_increments         - auto-increment counters (6 docs)
game_igl               - IGL leaderboard (1 doc)
game_blocs             - chat blocs (0 docs)

SCHEMA DETAILS
-------------

1. game_accounts
   _id: ObjectId (primary key)
   username: string
   email: string
   password: string (bcrypt $2a$10/12$... or Jasypt AES base64...)
   userRank: "USER" | "ADMIN"

2. game_users
    _id: ObjectId
    accountId: string (NOT ObjectId - stored as plain hex string)
    userId: Long (2,3,4,5,6 - the real player ID, used as link key)
    guid: Long (matches userId)
    username: string (in-game name: "earth", "hee", "tester", etc.)
    gameServerId: int (server cluster ID, 32)
    leagueCount: int (0=unranked, 3=bronze/silver?, max=3)
    ground: int (planet type/level being used: 0=default, 1=starter, 2=upgraded)
    gMapId: int (galaxy map ID, always 0)
    chargeFlag: int (0=free, 1=paid?, used in payment/upgrade checks)
    card1/2/3/Union/credit: int (commander card slots:
      card1, card2, card3 = individual equipped commander cards
      cardUnion = result of combining two cards of same level
      cardCredit = currency for card-related actions)
    NOTE: Cards combine star-over-star: two 1-star cards = one 2-star card,
    two 2-star cards = one 3-star, etc. Max level = 9 stars.
    consortiaId: int (-1=none, 2=yop corp)
    consortiaJob: int (-1=none, 0=Recruit, 1=Colonel, 2=Commandant, 3=Captain, 4=Soldier)
    consortiaUnionLevel: int (union building level in corp, -1 if none)
    consortiaThrow/consortiaShop: int (corp building upgrade cost contributions —
      consortiaThrow = gold/resource contribution amount for throw/attack building,
      consortiaShop = contribution amount for shop/mall building.
      -1 = not contributed, 0 = contributed 0, positive = amount contributed.
      Corps have separate wealth; these track individual member upgrade payments.)
    tollGate: int (PvP toll/gate fee counter — in certain PvP modes
      (league/championship), players pay an entry toll to join.
      This field accumulates the total toll amount owed/paid.
      Always 0 in current data — either never used or always paid.)
    warScore: int (war points from corp wars)
    noviceGuide: int (tutorial progress flag, 0=complete)
    lastRecruit: ISODate (last time recruited a friend)
    toSave: boolean (dirty flag for persistence)
    notDisturb: boolean (DND mode for chat/notifications)
    pirateReceived: boolean (has pirate attack reward been claimed?)
    userMaxPpt: int (max packets-per-second allowed before flood flag, 0=default)
    year/month/day: int (calendar data, always 0 in current data)
    shipSpeedCredit: int (speed boost currency for ships)
    lotteryStatus: int (daily lottery state)
    freeSpins: int (daily wheel spin count remaining)
    lastSpin: ISODate (last time wheel was spun)
    sp: int (skill points / ability points)
    nextInvitation: ISODate (IGL match invite cooldown)
    restrictedUsedEntries/raidAttempts/raidIntercept: int (IGL restricted mode uses)
    instance: int (highest instance level completed)
    trial: int (trial mode flag)
    kills: int (total kills across all battles)
    collectedPoints: boolean (daily point collection flag)

    EMBEDDED PLAYER DATA:
    game_resources: {gold, he3, metal, vouchers, mallPoints, coupons, corsairs, honor, badge, championPoints}
    game_stats: {level, exp, sp, kills, instance, trial, restrictedUsedEntries,
                 raidAttemptsEntries, raidInterceptEntries,
                 nextInvitation, collectedPoints,
                 buffs: [{gameBoostId, until}],
                 leagueStats: {wins, losses, draws, league},
                 champStats: {points, wins, shootdowns},
                 iglStats: {claimed, entries, fleetIds[], rank}}
    game_ships: {ships: [{shipModelId, num}], factory[], repair[]}
    game_buildings: {buildings: [{index, buildingId, levelId, x, y, updating, untilUpdate, repairing}]}
    game_tasks: {currentMain, currentSide[], currentDaily[], completed[], dailyPoints, claimedDailyAwards[]}
    game_user_inventory: {maximumStacks, stackPrice, propList: [{propId, propNum, propLockNum, storageType, reserve}]}
    game_user_emails: {userEmails: [{autoId, type, readFlag, subject, emailContent, date, name, guid, fightGalaxyId, mailType?, goods: [{goodId, num, lockNum}]}]}
    game_user_techs: {techs: [{_id, level}]}
    game_bionic_chips: {phases[], slots, chips: [{chipId, chipExperience, holeId, bound}]}
    game_resource_storage: {gold, he3, metal, goldProduction, he3Production, metalProduction, lastProductionCalculus}
    game_rewards: {level, until} (VIP level and expiry)
    game_territories: {celestialHelpers[], territories: [{farmLandId, fieldId, desiredProduction, totalProduction, until, thieves}]}
    game_upgrades: {currentBodies: int[], currentParts: int[]} (ship designer unlocks)
    game_metrics: {metrics: [{identifier, value}]}
    game_user_friends: [] (friend list)

3. game_planets
    USER_PLANET schema (different from HUMAROID/RESOURCE):
      _id: ObjectId
      userId: Long (2,3,4 - links to game_users.userId)
      type: "USER_PLANET"
      position: {x, y}
      userObjectId: string (matches game_users._id)
      starFace: int (cosmetic/star display index, always 0)
      untilFlag: ISODate (attack protection expiry — new player immunity window)
      _class: "com.go2super.database.entity.sub.HumaroidPlanet"

      NOTE: untilFlag = protection timer. After this date, planet can be
            attacked/PvP. Same day as account creation for all 3 users.
            starFace appears cosmetic — always 0 in current data.

    HUMAROID_PLANET / RESOURCES_PLANET schema:
      _id: ObjectId
      userId: Long (null for NPC planets)
      type: "HUMAROID_PLANET" | "RESOURCES_PLANET"
      position: {x, y}
      currentLevel: int
      currentCorp: int
      destroyed: boolean
      peace: boolean
      statusTime: ISODate
      _class: "com.go2super.database.entity.sub.HumaroidPlanet"

    NOTE: USER_PLANET has NO currentLevel/destroyed/peace/statusTime fields.
          Planets have NO "name" field — identified by type + position + userId.

KEY RELATIONSHIPS
-----------------
game_accounts._id (ObjectId) ──→ game_users.accountId (string, plain hex)
         ↓
game_users.userId (Long) ──────→ game_planets.userId (Long)

- 1 account → 1 game_user (or none if account never logged in)
- 1 game_user → 1 USER_PLANET (or none if deleted/deprovisioned)
- game_users without planets: terrqa (uid 5), Delk (uid 6)

PASSWORD STORAGE
----------------
bcrypt ($2a$10/12$)  - admin, testuser, testuser2, tester, Delk
Jasypt AES (base64)  - iptest, iptest2, iptest3 (all decrypt to "test123")
   Key: 6c4c0cc399f655b313b1719287b3fde1 (MD5-based AES ECB)

DASHBOARD ADMIN
--------------
email: admin@supergo2.com
password: Ff5E!68a*5on (bcrypt work factor 10)
Stored in: game_dashboard_accounts

CURRENT ONLINE PLAYERS
----------------------
- hee (admin, uid 3) - chatting, testing fleet battles
- 1 connection total

CREDENTIALS (application.yml dev profile defaults)
-------------------------------------------------
MongoDB:     galaxybot / Hak4oYk44ZahfRrepkFc
hCaptcha:    0x078E2EbD57d43A6c7166ae87f3A86B9E6671eceD
SMTP:        master@supergo2.com / changeme
Dashboard:   admin@supergo2.com / Ff5E!68a*5on

CLOUD SHELL: mongosh "mongodb://galaxybot:Hak4oYk44ZahfRrepkFc@127.0.0.1:27017/go2super"


====================================================================
ITEMS / MODELS / INVENTORY / SHIPS
====================================================================

4. game_models (184 ship templates)
   _id: ObjectId
   shipModelId: int (0-180+, unique)
   guid: int (-1 for templates)
   name: string ("Wikes", "Battleship-A", "Pirate-C3", "Flagship-22", etc.)
   bodyId: int (ship body class id)
   deleted: boolean
   parts: int[] (array of part IDs making up this ship model)
   _class: "com.go2super.database.entity.ShipModel"

   Categories by name prefix:
     Wikes, Estrella, Parke, Wanderer, Bomber, Tiaz, Nadesico... (regular ships)
     Pirate-A1 through Pirate-I4 (pirate/humaroid ships)
     Capricornus-1 through Capricornus-5 (constellation ships)
     Flagship-1 through Flagship-25 (flagship ships)
     Virgo-1 through Virgo-5
     Killer-1 through Killer-4
     Star-1 through Star-23
     Boss-1 through Boss-4, Boss-Attack
     Max-A through Max-D
     Jumper-A, Jumper-B
     Tracker-A, Tracker-B
     Vortex-A, Vortex-B
     and more...

5. game_user_inventory (embedded in game_users)
   maximumStacks: 30
   stackPrice: 1000
   propList: [
     {propId: int, propNum: int, propLockNum: int, storageType: int, reserve: int}
   ]

   Known propId values:
     903 = resource item (metal?)
     917 = resource item
     (tester uid 4 has: 917x4, 903x2 in storage)

   PropId ranges by type (mimeType from game_boosts):
     900 = construction slots buff
     902, 937 = planet protection buff
     905 = basic metal production buff
     906 = basic he3 production buff
     907 = basic gold production buff
     930 = advanced gold production buff
     943 = MVP buff (ship building, repair, construction, daily draws, resources)
     979 = Christmas buff
     4458 = GF buff (resource production, ship building/repair)
     4513 = Halloween buff
     939-942 = luxurious/metallic/gaseous/ordinary planet buffs

   Storage types:
     storageType: 0 = main storage
     propLockNum = locked/pending items
     reserve = reserved items

6. game_ships (embedded in game_users)
   ships: []         (active fleet ships, ShipSlot[])
   factory: []       (ship construction queue, FactoryShip[])
   repair: []        (ship repair queue, FactoryShip[])

7. game_buildings (embedded in game_users)
   buildings: [
     {
       index: int (slot position)
       buildingId: int (type of building)
       levelId: int (current level)
       x: int, y: int (pixel coordinates)
       updating: boolean
       untilUpdate: ISODate (if upgrading)
       repairing: boolean
     }
   ]

   Building IDs (known):
     0 = command center / HQ
     1 = metal mine
     2 = he3 extractor
     3 = gold refinery
     4 = shipyard
     5 = warehouse
     6 = radar
     7 = space station
     9 = trading post
     10 = research lab
     11 = alliance center
     12 = defense turret
     13 = solar plant
     14 = repair bay
     19-32 = additional building types
     30 = special building

8. game_user_techs (embedded in game_users)
   techs: [{_id: int, level: int}]
   Known: tech _id 100 = starting tech (level 1)

9. game_bionic_chips (embedded in game_users)
   phases: [1,0,0,0,0] (5 phases unlocked)
   slots: int (available chip slots)
   chips: [{chipId: int, chipExperience: int, holeId: int, bound: boolean}]
   chipId 3579 = common chip, 3819/3619/3539/3699 = commander gems

10. game_commanders (7 docs)
    commanderId: int (unique per user)
    userId: Long (matches game_users.userId)
    name: string ("commander:essido", "commander:raysOfDestiny", "Commander")
    skill: int (commander power stat)
    stars: int (0-8)
    level: int
    experience: int
    variance: int
    dead: boolean
    injuredMatch: string (match UUID if injured)
    growthAim/Dodge/Speed/Electron: int (growth stats)
    gems: int[] (12 slots, -1 = empty, chipId = equipped gem)
    chips: [{chipId, chipExperience, holeId, bound}]
    commonBaseAim/Dodge/Speed/Electron: int
    commonExpertise: {"ballistic":"C","directional":"D",...} (expertise levels A-E)
    shipTeamId: int (-1 if not assigned to fleet)
    _class: "com.go2super.database.entity.Commander"

11. game_team_models (2 docs) - fleet templates
    _id: ObjectId
    guid: int (player guid)
    indexId: int (slot 0-1)
    teamModel: {"model":[{"shipModelId":int,"num":int},...]} (9 entries of shipModelId + count)
    _class: "com.go2super.database.entity.TeamModelSlot"

12. game_fleets (31 docs) — full schema
    _id: ObjectId
    shipTeamId: int (unique, matches FleetCache index)
    guid: int (owner player guid — THIS is the owner link, NOT userId!)
    name: string ("Enter-Fleet", "Undefined: challenge4a/b/c/d")
    commanderId: int (assigned commander for this fleet)
    he3: int (fuel consumed by fleet)
    bodyId: int (ship body class of fleet leader)
    rangeType: int (fleet range classification)
    preferenceType: int (battle preference)
    posX: int, posY: int (current position)
    direction: int
    match: boolean (is in a match)
    additionalGrowth: int (extra growth stat)
    forceTechs: boolean (ignore tech bonuses?)
    galaxyId: int (-1 = unassigned)
    fleetBody: {cells: [{shipModelId: int, num: int}, ...]} (9 cells)
    fleetMatch: {match: UUID, matchType: "INSTANCE_MATCH"|"PVP_MATCH", galaxyId: int}
    fleetInitiator: {jumpType: "RECALL"|?} (return-to-base action)
    _class: "com.go2super.database.entity.Fleet"

    NOTE: Fleet owner is tracked by `guid` field, NOT userId.
          The game_fleets.userId field doesn't exist in this schema.
          IGL player has fleetIds[] referencing shipTeamId values.
          shipModelId 52 = "New-H" in game_models (leet code for 3000 ships)


====================================================================
BOOSTS / BUFFS
====================================================================

13. game_boosts (16 boost definitions, not instances)
    _id: ObjectId
    propId: int (unique)
    mimeType: int (category)
    bonuses: string[] (e.g. "CONSTRUCTION_SLOTS", "PLANET_PROTECTION", etc.)
    seconds: int (duration)
    _class: "com.go2super.database.entity.GameBoost"

    mimeType → category mapping:
    0  = Construction Slot Boost
    1  = Planet Protection
    2  = Basic Metal Production
    3  = Basic He3 Production
    4  = Basic Gold Production
    5  = Advanced Gold Production
    6  = Truce Impediment
    7  = MVP Boost (all bonuses)
    10 = Luxurious Gold Production
    11 = Metallic Metal Production
    12 = Gaseous He3 Production
    13 = Ordinary Planet
    14 = Christmas Boost
    15 = GF (Galaxy Fleet) Boost
    16 = Halloween Boost

    Bonus types (from bonuses[]):
    CONSTRUCTION_SLOTS, PLANET_PROTECTION, TRUCE_IMPEDIMENT,
    BASIC_METAL_RESOURCE_PRODUCTION, BASIC_HE3_RESOURCE_PRODUCTION,
    BASIC_GOLD_RESOURCE_PRODUCTION, ADVANCED_GOLD_RESOURCE_PRODUCTION,
    MVP_SHIP_BUILDING_RATE, MVP_SHIP_REPAIRING_RATE, MVP_CONSTRUCTION_SPEED,
    MVP_DAILY_DRAWS_BONUS, MVP_RESOURCE_PRODUCTION,
    PLANET_APPEARANCE, CHRISTMAS_RESOURCE_PRODUCTION, CHRISTMAS_SHIP_BUILDING_SPEED,
    GF_RESOURCE_PRODUCTION, GF_SHIP_BUILDING_SPEED, GF_SHIP_REPAIRING_SPEED,
    LUXURIOUS_GOLD_RESOURCE_PRODUCTION, METALLIC_METAL_RESOURCE_PRODUCTION,
    GASEOUS_HE3_RESOURCE_PRODUCTION, ORDINARY_PLANET

    Active player buffs (from game_users.game_stats.buffs[]):
    tester (uid 4) and terrqa (uid 5) both have:
      gameBoostId: ObjectId("6a019b2395a0532ad07725c6") = propId 937 (PLANET_PROTECTION)
      until: ~2026-05-22 (3 days from now)


====================================================================
RESOURCES / PRODUCTION
====================================================================

14. game_resources (embedded in game_users)
    gold: Long, he3: Long, metal: Long
    vouchers: Long, mallPoints: Long, coupons: Long
    corsairs: Long, honor: Long, badge: Long
    championPoints: Long, freeSpins: int

    Max per resource: 999,999,999 (from UserResources.MAX_RESOURCES)

15. game_resource_storage (embedded in game_users)
    gold, he3, metal: current stockpile amounts
    goldProduction, he3Production, metalProduction: per-hour output
    lastProductionCalculus: ISODate (for offline production calculation)


====================================================================
TRADES / STORE / ECONOMY
====================================================================

16. game_trades (1 active listing)
    tradeId: int
    propId: int (item being sold)
    sellerUserId: Long
    sellerGuid: int
    sellId: int
    amount: int (quantity)
    price: int
    priceType: "GOLD" (or other currency)
    tradeType: "GEM" (or other)
    until: ISODate (listing expiry)

17. game_store_events (1 doc)
    accountId: string
    storePoints: Long
    events: [] (empty - no active store events)


====================================================================
CORPS / ALLIANCES
====================================================================

18. game_corps (1 corp: "yop")
    corpId: int (2 — separate from _id)
    name: string ("yop")
    philosophy: string
    bulletin: string
    level: int, mallLevel: int, mergingLevel: int, warehouseLevel: int
    piratesLevel: int, fees: int (corp trading fee tax — each member trade
      may contribute `fees` amount to corp wealth treasury)
    maxMembers: int, contribution: int, wealth: int
    icon: int
    resourceBonus: float (0.5 = 50% bonus to resource production)
    mergeBonus: float (0.4 = 40% bonus to corp merging)
    rbpLimit: int (10 = RBP planet capture limit)
    contributionMerge: int (-1 = not configured/disabled)
    contributionMall: int (-1 = not configured/disabled)
    planets: int, territories: int
    corp_members: {members: [{guid, rank, contribution, donateResources, donateMallPoints}], recruits: []}
    corp_history: {incidents: [{type, date, sourceName, objectName, sourceUserId, sourceObjectId, guid, extend, incidentType}]}
    consortiaJobName: {name0:"Recruit",name1:"Colonel",name2:"Commandant",name3:"Captain",name4:"Soldier"}
    _class: "com.go2super.database.entity.Consortia"

    Corp ranks: 0=Recruit, 1=Colonel, 2=Commandant, 3=Captain, 4=Soldier
    Incident types: CONTRIBUTE, PLANET_SEIZED, BUILD_UPGRADE, ATTACK_SUCCESSFUL, ATTACK_FAILED
    contributionMerge/contributionMall = -1 means feature is disabled/not configured


====================================================================
TASKS / QUESTS / DAILY
====================================================================

19. game_tasks (embedded in game_users)
    currentMain: {taskId, type:0, level, value, complete, obtainable, redeemed}
    currentSide: [] (side quests, same structure)
    currentDaily: [] (daily quests, type:2)
    completed: [] (finished tasks, preserved for record)
    dailyPoints: int (0-134, tracks daily quest progress)
    claimedDailyAwards: int[] (award IDs already claimed today)

    Task types: 0=main, 1=side, 2=daily
    Daily points thresholds: Bronze=10, Silver=30, Gold=50, Diamond=70

20. game_metrics (embedded in game_users)
    metrics: [{identifier: string, value: int}]
    Known identifiers:
    action:use.anypack, action:harvest, action:speedup.construction,
    action:send.message, action:send.any, etc.


====================================================================
IGL / LEAGUE / CHAMPIONSHIP
====================================================================

21. game_igl (1 doc)
    userId: Long
    fleetIds: [1538, 1535, 1536, 1537] (4 fleet shipTeamIds registered for IGL)

    IGL fleets match game_fleets entries:
    shipTeamId 1535-1538 = "Enter-Fleet" (hee/tester IGL team)
    shipTeamId 2517-2519 = "Undefined: unknown17/18" (NPC opponents)
    shipTeamId 2520-2538 = "Undefined: challenge4a/b/c/d" (challenge mode fleets)


====================================================================
AUTO-INCREMENTS (ID counters)
====================================================================

game_planets => 5
game_users => 5
game_commanders => 460
game_models => 176
game_fleets => 2519
game_corps => 2


====================================================================
SESSION / AUTH / SECURITY
====================================================================

22. game_account_sessions (5 active)
    accountId: string (matches game_accounts._id)
    token: string (64-char hex, SecureRandom)
    expired: boolean
    loginDate: ISODate
    untilDate: ISODate (30-day expiry)

23. game_dashboard_account_sessions (116 sessions)
    Same structure as game_account_sessions
    Has ipAddress field for IP-binding audit
    Note: 109 sessions have null ipAddress (old records before IP binding)

24. game_users_ips (6 records)
    email, accountId, accountName
    ips: [{accountId, guid, userId, username, ip, count, lastTime}]
    Tracks IP per account, all from 10.0.2.2 (VirtualBox NAT host)

25. game_risk_incidents (2 incidents)
    a) SameIPIncident (10.0.2.2) - 3 users from same IP: earth, hee, Delk
    b) PacketFloodIncident (hee/uid 3) - 125 reports, packet types 1530/1250/1059
       ppt: 0.29 (packets per second threshold exceeded)