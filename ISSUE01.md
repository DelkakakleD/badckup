# ISSUE01 — Ship Build Timer & Factory UI

## Symptoms
1. Ships completing instantly or at unpredictable times
2. Ship build factory timer showing wrong remaining time
3. Client not receiving updated factory state after ship completion
4. `onSpeedShip` (speed-up) returning incorrect spareTime values
5. `onFactory` (open shipyard) not sending ship model list to client

## Root Causes

### 1. ShipConstructionJob — timeRemain double-counted in next interval
**File:** `GO2Server/src/main/java/com/go2super/service/jobs/user/ShipConstructionJob.java`

```java
// BUG: timeRemain is the REMAINING time from the previous while-loop iteration
// Adding it to buildTime*1000 causes the next interval to be EXTENDED by the
// negative timeRemain, progressively pushing the completion further into the future.
int next = (int) (factoryShip.getBuildTime() * 1000 + timeRemain);

// FIX: Just use buildTime*1000 as the clean next interval
int next = (int) (factoryShip.getBuildTime() * 1000);
```

The `timeRemain` variable holds `DateUtil.remainsMillis(factoryShip.getUntil())`. When `timeRemain <= 0` (ship is due), the `while` loop fires. Inside the `else` branch (more ships remain in the queue), the NEXT ship's timer was computed as `buildTime*1000 + timeRemain`. Since `timeRemain` is <= 0 (could be -500ms, -2000ms, etc.), this subtraction from the next interval meant subsequent ships appeared to complete increasingly early or late, accumulating error across the queue.

### 2. ShipConstructionJob — no factory info sent to client after completion
**File:** Same as above

```java
// BUG: After all ships in the queue are processed, the factory info packet
// (ResponseCreateShipInfoPacket) was never sent to the client. The client's
// shipyard UI remained stale until manually reopened.
if (save) {
    user.update();
    user.save();
    // Missing: send updated factory info to client
}

// FIX: Send factory info to client after every construction tick
if (save) {
    user.update();
    user.save();
    ResponseCreateShipInfoPacket factoryInfo =
        ShipFactoryListener.buildFactoryInfo(user);
    if (factoryInfo != null) {
        loggedUser.getSmartServer().send(factoryInfo);
    }
}
```

### 3. FactoryShip.needTime() — negative return values
**File:** `GO2Server/src/main/java/com/go2super/database/entity/sub/FactoryShip.java`

```java
// BUG: When remains goes negative (timer already expired but ship not yet
// processed by the job), the result can be negative. This propagates to the
// client as a garbled timer display.
public int needTime() {
    int remains = until != null ? DateUtil.remains(until).intValue() : 0;
    return remains + ((num - 1) * (int) buildTime);
}

// FIX: Clamp to 0 to prevent negative values reaching the client
public int needTime() {
    int remains = until != null ? DateUtil.remains(until).intValue() : 0;
    int b = (int) buildTime;
    int total = (num - 1) * b;
    return Math.max(0, remains + total);
}
```

### 4. ShipFactoryListener.onSpeedShip() — incorrect spareTime and early-exit check
**File:** `GO2Server/src/main/java/com/go2super/listener/ShipFactoryListener.java`

```java
// BUG 1: needTime used an outdated buildTime (pre-speed-up) for the
// remaining ships, giving the wrong spareTime to the client.
double buildTime = factoryShip.getBuildTime() / 1.1;   // new buildTime
double needTime = newRemains + (buildTime * (factoryShip.getNum() - 1));
//                          ^ was using the MODIFIED buildTime — OK
// But the original code used `buildTime` (already modified) — this was correct.
// However...

// BUG 2: The early-exit check was wrong. (needTime - num <= 0) doesn't
// make sense as an abort condition. It should check if remains <= 0.
if (needTime - factoryShip.getNum() <= 0) {
    return;   // Wrong: checks needTime, not remains
}

// FIX:
if (remains <= 0) {
    return;   // Correct: if there's no remaining time, abort
}
```

### 5. ShipFactoryListener.onFactory() — missing ship model list
**File:** Same as above

```java
// BUG: onFactory (triggered when player opens shipyard) only sent
// ResponseCreateShipInfoPacket (factory queue state) but NOT
// ResponseShipModelInfoPacket (available ship designs). The client
// displayed an empty ship model list.

// FIX: After sending factory info, also send ship models in batches of 7:
@PacketProcessor
public void onFactory(RequestCreateShipInfoPacket packet) throws BadGuidException {
    // ... auth & validation ...
    ResponseCreateShipInfoPacket factoryInfo = buildFactoryInfo(user);
    if (factoryInfo != null) {
        packet.reply(factoryInfo);
    }
    // NEW: Send ship model list in batches of 7
    try {
        List<ShipModel> models = PacketService.getInstance().getShipModelCache()
                .findAllByGuidAndDeleted(user.getGuid(), false);
        models.add(0, PacketService.getShipModel(0));
        ResponseShipModelInfoPacket pkt = new ResponseShipModelInfoPacket();
        for (ShipModel sm : models) {
            if (pkt.getShipModelInfoList().size() >= 7) {
                packet.reply(pkt);
                pkt = new ResponseShipModelInfoPacket();
            }
            pkt.getShipModelInfoList().add(ShipModelInfo.of(
                    sm.getName(), sm.partNum(), (char) 0, sm.getBodyId(),
                    sm.partArray(), sm.getShipModelId()));
        }
        if (pkt.getShipModelInfoList().size() > 0) {
            packet.reply(pkt);
        }
    } catch (Exception e) {
        BotLogger.error(e);
    }
}
```

## Files Changed

| File | Changes |
|------|---------|
| `FactoryShip.java` | `needTime()`: wrapped return with `Math.max(0, ...)` |
| `ShipConstructionJob.java` | Removed `+ timeRemain` from next interval calc; added factoryInfo push after save |
| `ShipFactoryListener.java` | New `buildFactoryInfo()` static method; `onFactory()` now sends ship models in batches; `onSpeedShip()` fixed early-exit and variable naming |
| `pom.xml` | `java.version` changed from 22 to 21 (build compat) |

## Debugging & Hotswap Patches

### LoginListener port patch (baked into JAR):
LoginListener was patched via hotswap to read port from system property:
```java
// Instead of: response.setPort(90);
int port = Integer.parseInt(System.getProperty("application.game.port", "90"));
response.setPort(port);
```
Systemd passes `-Dapplication.game.port=15090`, so the client receives `port=15090`.

### All hotswap patches baked into `game-server-patched.jar`:
- `SecurityHeadersFilter.class` — CSP headers
- `CommanderListener.class` — card draw fix
- `FleetListener.class` — debug logging removed
- `LoginListener.class` — port=System.getProperty("application.game.port")
- `PlayerListener.class` — INFODEL disabled
- `ShipFactoryListener.class` — our source fix compiled
- `TaskListener.class` — daily award fix
- `TradeListener.class` — ship model removal fix
- `PacketService.class` — getShipModels() fix

## Restore Point
**File:** `/opt/galaxybot/restore-points/galaxybot-restore-20260522_185412.tar.gz`
Contains: Patched JAR, MongoDB dump, systemd services, wsbridge, hotswap patches.
To restore: `tar -xzf ... && cd <dir> && bash restore.sh`

## Git Commit
`3a0ac4f` — local only (push blocked: `DelkakakleD` lacks access to `markowenpercy-ai/reimagined-octo-giggle`)
