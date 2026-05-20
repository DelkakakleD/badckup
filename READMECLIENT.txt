================================================================================
GALAXY BOT CLIENT ARCHITECTURE DOCUMENTATION
================================================================================

## OVERVIEW
Galaxy Bot is a browser-based MMO space strategy game using:
- Adobe Flash (ActionScript 3.0) for the game client
- Chromium Embedded Framework (CEFSharp) as the browser engine
- C# WPF launcher (.NET 4.0+) to host the Flash client
- SignalR over WebSocket for real-time communication
- REST API over HTTP for other operations

================================================================================
## CLIENT STRUCTURE
================================================================================

### Directory Layout
/home/kali/Desktop/DISTRO/
├── Galaxy Bot.exe          # Main WPF launcher (PE32 executable, 152KB)
├── Galaxy Bot.dll          # Embedded C# assemblies (costura/Fody-weaved, 1.4MB+)
├── GalaxyOrbit.Resources.dll  # Game resource handler (LZMA decompression)
├── SevenZip.dll            # 7-Zip LZMA compression library
├── libs/
│   ├── pepflashplayer.dll  # Adobe Pepper Flash (18MB)
│   └── eng.traineddata     # Tesseract OCR data (23MB)
├── gamedata/               # All game assets
│   ├── asset/
│   │   ├── client.go2      # Main game client SWF (700KB compressed)
│   │   ├── gameres.go2     # Game resources SWF (1MB+)
│   │   ├── games_asset.go2 # Games asset SWF (2MB+)
│   │   ├── picres.go2      # Picture resources (2MB)
│   │   ├── map_asset.go2   # Map assets (2.4MB, 560 images)
│   │   ├── airship.go2     # Airship sprites (1.2MB, 798 images)
│   │   ├── galaxy_asset.go2 # Galaxy assets (827KB)
│   │   ├── chat_asset.go2  # Chat assets (131KB)
│   │   ├── lottery.go2     # Lottery SWF (29KB + 1 image)
│   │   ├── afont.go2       # Font SWF (3KB)
│   │   ├── preloader_asset.go2 # Preloader assets (194KB)
│   │   ├── res/             # Building/MC sprites (20+ files)
│   │   └── music/           # Music/SFX (.go2 -> .mp3/.bin)
│   ├── data/
│   │   └── config.go2      # Game config XML (xmgo2 format)
│   ├── scripts/
│   │   ├── jquery.min.go2  # jQuery 3.6.4 (89KB JS)
│   │   └── loader.go2      # SWFObject 2.2 (12KB JS)
│   └── preloader.go2       # Preloader SWF (6KB)
├── host                    # Server endpoints config
├── CliBots/               # CLI bot tools
├── CommanderImageTool/     # Commander avatar tool
├── GO2Tool/               # .go2 file extractor/repacker
├── Images/                # UI images
└── cache/                  # Runtime cache

================================================================================
## .GO2 FILE FORMATS
================================================================================

Magic bytes determine file type:
- bngo2 (42 6E 67 6F 32) → .swf  (Flash movie)
- xmgo2 (78 6D 67 6F 32) → .xml  (XML config)
- mpgo2 (6D 70 67 6F 32) → .bin/.mp3 (Audio)
- jsgo2 (6A 73 67 6F 32) → .js   (JavaScript)
- imgo2 (69 6D 67 6F 32) → .jpg/.png (Image)

Extraction: dotnet GO2Tool.dll extract <file.go2> <output_dir>
Repacking:  dotnet GO2Tool.dll repack <source_dir> <output.go2>
Listing:    dotnet GO2Tool.dll list <file.go2>

GO2Tool source: /home/kali/Desktop/DISTRO/GO2Tool/
  - .NET 6 C# application
  - Handles LZMA decompression via SevenZip
  - Custom header format with version info

================================================================================
## GAME CLIENT FILES
================================================================================

### Main Client (client.go2/client.swf)
- Size: 699,964 bytes compressed → ~700KB SWF
- Contains: ActionScript 3.0 game logic, packet handlers, UI
- FlashVars configuration for server connection
- Connects to WebSocket at ws://localhost:9091

### Game Resources (gameres.go2/games_asset.go2/picres.go2)
- gameres.go2: 1,060,113 bytes - Core game resources
- games_asset.go2: 2,046,423 bytes - Additional game assets
- picres.go2: 1,517,778 bytes - Picture resources (963 images)
- Contain: Sprites, UI elements, ship graphics

### Map Assets (map_asset.go2)
- Size: 2,413,085 bytes (2.4MB)
- 560 embedded images (0-541 .jpg, 542-559 .png)
- Tile-based map system with terrain types

### Airship Sprites (airship.go2)
- Size: 1,254,318 bytes (1.2MB)
- 798 frames of airship animation (airship_000.jpg to airship_797.jpg)
- Frame rate and sprite sheet for ship animations

### Other Assets
- chat_asset.go2: 131,783 bytes - Chat UI assets
- lottery.swf: 29,606 bytes + 1 embedded image
- afont.swf: 3,089 bytes - Font definitions
- preloader.go2: 6,642 bytes - Loading screen

### Building Sprites (res/ directory)
- Multiple .go2 files for building animations
- Examples: citycentermc.go2 (83KB), repaircenter.go2 (218KB)
- Use MovieClip format for multi-frame animations

### Map Tiles (asset/map/)
- 4 map types: 0=desert, 1=snow, 2=load, plus others
- Each tile: 4 variations (_00 to _03)
- Format: imgo2 → .jpg, ~20-50KB each

### Music/SFX (asset/music/)
- galaxy.go2: Main theme (~1MB .mp3)
- battle.go2: Battle music (~498KB)
- Various SFX: eshipbase, ecommander, ebomb, eshipblast, etc.
- Format: mpgo2 → .bin audio files

================================================================================
## CONFIG.XML STRUCTURE
================================================================================

<?xml version="1.0" encoding="utf-8"?>
<config>
  <resources path="https://localhost/"
    gMap="asset/map/" res="asset/" client="asset/"
    galaxyAssetPath="galaxy_asset">

    <!-- SWF Resources -->
    <resource name="GameRes" src="gameres.swf" type="Mc" />
    <resource name="games_asset" src="games_asset.swf" type="Mc" />
    <resource name="Picres" src="picres.swf" type="Mc" />
    <resource name="lottery" src="lottery.swf" type="Mc" />
    <resource name="map_asset" src="map_asset.swf" type="Mc" />
    <resource name="Airship" src="airship.swf" type="Mc" />
    <resource name="chat" src="chat_asset.swf" type="Mc" />
    <resource name="font" src="afont.swf" type="Mc" />

    <!-- Music -->
    <music path="https://localhost/" res="asset/music/">
      <audio name="galaxy_music" src="galaxy.mp3" type="Sound" />
      <audio name="battle_music" src="battle.mp3" type="Sound" />
      <!-- + 10+ SFX audio files -->
    </music>
  </resources>

  <Note>
    <!-- Loading messages -->
    <Msg name="loadLoginServer" src="Connecting to the login server." />
    <Msg name="loadGameServer" src="Connecting to the game server." />
    <!-- ... -->
  </Note>
</config>

================================================================================
## LAUNCHER ARCHITECTURE (Galaxy Bot.exe)
================================================================================

### Technology Stack
- .NET Framework 4.0+ (WPF application)
- CefSharp WinForms 87.1.132.0 (Chromium Embedded Framework)
- Microsoft.AspNet.SignalR.Client 2.4.3.0
- SevenZip LZMA for resource decompression
- Costura/Fody for assembly embedding

### Key Components

1. FlashPolicyListener
   - Listens on a TCP port for Flash policy requests
   - Returns cross-domain policy for Flash socket connections

2. ChromiumWebBrowser (CEFSharp)
   - Hosts the game HTML/Flash content
   - Handles URL loading via GetIFrameUrl from server
   - No native Flash plugin - uses Pepper Flash from libs/

3. GO2HttpService
   - REST API client for HTTP operations
   - Login, CreatePlanet, GetPlanets, GetOnlinePlayers
   - GetVersion, CheckClientGOFiles (updates)
   - GetData, PostFormData, UploadImage
   - ChangePassword

4. WebSocketProxy
   - Manages SignalR WebSocket connection
   - GetWebSocketAuth for authentication
   - Listen, Receive, Send operations
   - DetectDisconnect for connection monitoring

5. GalaxyOrbit.Resources (embedded DLL)
   - Handles .go2 file format detection (imgo2, xmgo2, bngo2, mpgo2, jsgo2)
   - LZMA decompression of embedded resources
   - SevenZip.BindZipArchive for archive handling

### Communication Flow

User launches "Galaxy Bot.exe"
    ↓
CefSharp browser initializes
    ↓
HTTP REST Call → GET /api/client/getIFrameUrl
    ↓
Returns HTML page URL with Flash embeds
    ↓
Browser loads HTML → includes SWFObject + jQuery
    ↓
SWFObject embeds client.swf with FlashVars
    ↓
Flash client connects via SignalR WebSocket
    ↓
Real-time game communication over ws://localhost:9091

### Server Endpoints (from host file)
http://localhost:9090  → REST API server
ws://localhost:9091    → WebSocket (SignalR) server

================================================================================
## FLASH CLIENT (client.swf)
================================================================================

### Technology
- Adobe Flash 10+ (ActionScript 3.0)
- Compressed SWF format
- SWFObject 2.2 for embedding
- jQuery 3.6.4 for DOM manipulation

### FlashVars Configuration
The client.swf receives FlashVars including:
- serverUrl: Game server HTTP endpoint
- wsUrl: WebSocket endpoint
- resourcePath: Base URL for assets
- version: Client version for update checking

### Packet Protocol
Client communicates via ActionScript MessageChannel/NetConnection:
- Binary AMF or custom binary protocol over WebSocket
- Packet structure: [type:int16][length:int32][data:bytes]
- Types: 1=Login, 2=Logout, 3=MoveFleet, 4=Attack, etc.

### Key Flash Classes (from decompilation hints)
- GameClient: Main game controller
- PacketHandler: Server message processing
- FleetManager: Fleet creation/movement
- PlanetManager: Base management
- BattleProcessor: Combat resolution
- MapRenderer: Galaxy/galaxy map display

================================================================================
## SIGNALR WEBSOCKET PROTOCOL
================================================================================

### Authentication Flow
1. HTTP POST /api/client/login (username, password)
2. Server returns session token
3. HTTP GET /api/client/getWebSocketAuth
4. Returns WebSocket auth token
5. Connect to ws://localhost:9091 with auth token
6. SignalR negotiation: /signalr/hubs

### Message Format
SignalR messages are JSON with structure:
{
  "H":"GameHub",
  "M":"MethodName",
  "A":[arg1, arg2, ...]
}

Examples:
- {"H":"GameHub","M":"MoveFleet","A":[fleetId, fromPlanet, toPlanet]}
- {"H":"GameHub","M":"AttackPlanet","A":[fleetId, targetPlanetId]}

### Hub Methods
GameHub (main game operations):
- MoveFleet, AttackPlanet, RecallFleet
- BuildShip, UpgradeBuilding, ResearchTech
- SendMessage, JoinCorp, CreateCorp
- GetMapData, GetPlanetDetails

================================================================================
## EXTRACTED FILES LOCATIONS
================================================================================

/tmp/go2_extract/
├── client.swf           # Main client (700KB)
├── gameres.swf          # Game resources (1MB)
├── games_asset.swf      # Games assets (2MB)
├── games_asset_*.jpg    # 71 asset images
├── picres.swf           # Picture resources (2MB)
├── picres_*.jpg         # 963 picture images
├── picres_*.png         # 13 PNG images
├── galaxy_asset.swf     # Galaxy assets (827KB)
├── galaxy_asset_*.jpg   # 273 galaxy images
├── map_asset.swf        # Map assets (2.4MB)
├── map_asset_*.jpg      # 543 map tiles
├── map_asset_*.png      # 17 PNG overlays
├── airship.swf          # Airship sprites (1.2MB)
├── airship_*.jpg        # 798 airship frames
├── chat_asset.swf       # Chat assets
├── chat_asset_*.jpg     # Chat images
├── lottery.swf         # Lottery SWF + 1 image
├── afont.swf           # Font definitions
├── jquery.js           # jQuery 3.6.4
├── loader.js           # SWFObject 2.2
├── config.xml         # Resource manifest
├── preloader.swf     # Preloader
├── jquery.min.js     # (from scripts/jquery.min.go2)
└── loader.js         # (from scripts/loader.go2)

/tmp/go2_extract/extra/  (additional extracted go2 files)
/tmp/go2_extract/js/     (extracted JavaScript)
/tmp/go2_extract/map/    (extracted map tiles)

================================================================================
## UPDATE MECHANISM
================================================================================

Client checks for updates via GO2HttpService.CheckClientGOFiles:
- Sends list of local .go2 file hashes
- Server responds with missing/outdated files
- Returns URL to download new version

GetNewVersionUrl returns update server URL.

Update flow:
1. Client sends GET /api/client/checkClientGOFiles
2. Body: JSON array of {filename, hash} objects
3. Response: {needsUpdate: bool, files: [{name, url, hash}]}
4. Client downloads from url and replaces local files

================================================================================
## KEY BINARIES & TOOLS
================================================================================

GO2Tool (custom .go2 extractor/repacker)
Location: /home/kali/Desktop/DISTRO/GO2Tool/
Command: dotnet GO2Tool.dll <extract|repack|list> <input> [output]

Galaxy Bot Launcher
Location: /home/kali/Desktop/DISTRO/Galaxy Bot.exe
Type: PE32 executable (WPF/.NET)
Dependencies: Galaxy Bot.dll, GalaxyOrbit.Resources.dll, SevenZip.dll
Runtime: CefSharp (Pepper Flash in libs/pepflashplayer.dll)

MongoDB Connection
- Database: go2super
- User: galaxybot
- Password: Hak4oYk44ZahfRrepkFc (from application.yml)
- Auth URI: mongodb://galaxybot:Hak4oYk44ZahfRrepkFc@127.0.0.1:27017/go2super

================================================================================
## JAVASCRIPT FILES
================================================================================

### jQuery 3.6.4 (jquery.min.go2 → jquery.min.js)
- 89,795 bytes minified
- Used for DOM manipulation in HTML loader page
- Provides: $.ajax for HTTP, event handling, animation

### SWFObject 2.2 (loader.go2 → loader.js)
- 12,325 bytes
- Embeds Flash SWF in HTML pages
- Handles: detection, embedding, dynamic loading
- FlashVars passing to SWF

================================================================================
## SHIP MODEL DATA (from MongoDB game_models collection)
================================================================================

Sample ships (shipModelId → name):
0: Wikes (bodyId: 0)
1: Estrella-A (bodyId: 64)
3: Parke (bodyId: 32)
6: RV369 (bodyId: 67)
7: Bomber (bodyId: 34)
9: Battleship-A (bodyId: 37)
10: Tiaz (bodyId: 70)
15: Interceptor (bodyId: 73)
52: New-A (leet ship, bodyId: 98)

Ship model fields:
- shipModelId: Unique ID
- name: Display name
- bodyId: Body/sc hull template (0-324)
- parts: Array of part IDs for ship composition
- guid: Owner override (-1 for templates)
- deleted: Soft delete flag
- _class: 'com.go2super.database.entity.ShipModel'

================================================================================
## ROOM FOR FURTHER RESEARCH
================================================================================

1. Decompile client.swf (FFDEC not yet working - needs Java runtime)
   - Extract ActionScript packet definitions
   - Analyze game logic classes
   - Find encryption/obfuscation details

2. Decompile gameres.swf
   - Extract embedded sprites/images
   - Analyze UI component library

3. Parse Galaxy Bot.exe with proper .NET decompiler
   - Full method analysis
   - Understand update mechanism completely

4. Analyze SignalR hub protocol
   - Capture actual traffic
   - Document all hub methods

5. Map tile format analysis
   - How tiles are composed into galaxy maps
   - Coordinate system

6. Packet encryption
   - Whether packets are encrypted
   - Key exchange mechanism
================================================================================
## PROTOCOL ANALYSIS (Updated with Traffic Capture)
================================================================================

### Discovered API Endpoints

Traffic capture from external client (10.0.2.2) shows:

1. GET /metrics/online (polled every ~30 seconds)
   Request: GET /metrics/online HTTP/1.1
            Host: 127.0.0.1:9090
            User-Agent: Mozilla/5.0...supergo2-beta/1.0.0-beta Chrome/85.0.4183.121
            Authorization: 41c90317c72613... (JWT token)
   Response: {"code":200,"message":"OK","data":{"online":1}}

2. GET /realtime/auth?hwid={hwid} (WebSocket auth)
   Returns JWT for SignalR connection

3. GET /accounts/play/user/{planetId}
   Returns HTML iframe URL for game loading

### HTTP Headers Observed
- origin: http://127.0.0.1:9090
- referer: http://127.0.0.1:9090
- User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 
              (KHTML, like Gecko) supergo2-beta/1.0.0-beta Chrome/85.0.4183.121 
              Electron/10.1.3 Safari/537.36
- Authorization: Bearer {JWT_TOKEN}

### WebSocket (Port 9091) Protocol
- Uses SignalR with JWT authentication
- Bearer token passed in WebSocket upgrade request
- Binary frames after upgrade (not HTTP)

### Authentication Flow
1. HTTP POST /login/login/account → {token}
2. HTTP GET /realtime/auth?hwid={HWID} → {JWT for WS}
3. WebSocket upgrade with "Authentication: Bearer {JWT}" header
4. SignalR hub communication over WebSocket

### HWID (Hardware ID) Generation
From C# decompiled code - HwidParser.Value():
- CPU: Win32_Processor.UniqueId/ProcessorId/Name/MaxClockSpeed
- BIOS: Manufacturer+SMBIOSBIOSVersion+IdentificationCode+SerialNumber+ReleaseDate+Version
- Disk: Model+Manufacturer+Signature+TotalHeads
- Baseboard: Model+Manufacturer+Name+SerialNumber
- Video: DriverVersion+Name
- MAC: MACAddress (IPEnabled)
- Combined string hashed with MD5 to GUID

================================================================================
## KEY FILES LOCATIONS - FINAL SUMMARY
================================================================================

Decompiled ActionScript (/tmp/swfs_decompiled/):
- /tmp/swfs_decompiled/scripts/Client.as - Main entry point, FlashVars handling
- /tmp/swfs_decompiled/scripts/net/base/NetManager.as - Socket connection management
- /tmp/swfs_decompiled/scripts/net/router/GameRouter.as - Game message routing
- /tmp/swfs_decompiled/scripts/net/router/FleetRouter.as - Fleet operations
- /tmp/swfs_decompiled/scripts/net/router/CustomRouter.as - Custom responses

Decompiled .NET (/tmp/dotnet_decompiled/):
- /tmp/dotnet_decompiled/galaxy_bot_dll/Galaxy Bot.decompiled.cs (9111 lines)
  Contains: GO2HttpService, WebSocketProxy, FlashPolicyListener, BotControl

Traffic Capture (/tmp/traffic_capture/):
- game_external.pcap - 16 packets captured (external client traffic)

================================================================================
