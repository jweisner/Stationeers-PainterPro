# AGENTS.md

Working notes for anyone (human or agent) changing this mod. Controls, install and
build basics are in [README.md](README.md); this file covers how it works and how to
work on it.

## Status (2026-11-14)

- **1.0 released**: GitHub release `v1.0` and Steam Workshop item
  [3840045914](https://steamcommunity.com/sharedfiles/filedetails/?id=3840045914) (public).
- Tested: single player with Shift and Ctrl on pipes (including long pipes), cables
  (including long cables) and chutes; a remote client on a dedicated server with pipes.
- **Not tested**: robotic arm rails anywhere; a listen-server host with a remote client.
- No open task.

## How it works

PainterPro is a full rewrite with no code from NetworkPainter (it began as a fork of
Elmotrix/NetworkPainter, which has no license; the README credits it as inspiration).
One Harmony patch and one network message:

- `SprayPatch`: postfix on `OnServer.AttackWith`. That method runs only on the
  machine whose player used the tool, so it fires once per spray where the keys can
  be read. No Shift/Ctrl, no sprayer, no paint, or gun off: do nothing. Otherwise it
  builds a `PaintRequest {PainterId, HandSlot, TargetId, ColorIndex, Mode}`.
- `GameManager.RunSimulation` (single player and the listen host): call
  `NetworkPaint.Apply` directly. Remote client: `PaintRequestMessage.SendToHost()`,
  whose `Process` calls the same `Apply`.
- `NetworkPaint.Apply` checks the painter's hand slot holds an `ISprayer`, then
  paints the network. It never paints the sprayed target itself: vanilla does that
  and charges paint for it, and pre-painting it would make vanilla refuse ("already
  that colour") if our message arrived first.
- Checkered: one hop-counting BFS (`PaintCheckered<T>`) for every network type.
  Pipes, chutes and rails get neighbours from `ConnectedStructures()`. Cables are
  not `INetworkedStructure`, so `ConnectedCables` replicates the game's
  `SmallGrid.FillConnected` (whose `Span<>` signature is unusable from net472).
  Members the walk never reaches get their own walk, seeded by cell parity.

**Paint scope on pipe networks is pipe segments only** (`item is Piping`, which
includes `PipingLong`). Everything else deriving from `Pipe` is a device on the run
(in-line tanks, vents, drains, connectors, organ pipes, planters) and is left alone:
checkered paint marks a gas mix, and a tank taking one arbitrary half of the pattern
would be wrong half the time. The filter is an allow-list on purpose so devices the
game adds later are excluded automatically. Spraying a `HydroponicTray` paints trays,
a `PassiveVent` paints vents. Rails skip `RoboticArmDock`. Things with
`HasColorState` are skipped, as vanilla does.

**Order independence is required.** LaunchPad sends mod messages on its own
transport channel (`(NetworkChannel)169`); the game uses `GeneralTraffic`. Ordering
is only guaranteed within a channel, so the paint message can arrive before or after
the vanilla `AttackWithMessage`. Keep every message self-contained and safe in
either order.

## Layout and build

| Path | Contents |
|---|---|
| `PainterPro/PainterProPlugin.cs` | BepInEx entry point: registers the message, patches `SprayPatch` in a try/catch |
| `PainterPro/SprayPatch.cs` | `AttackWith` postfix: reads keys, builds the request |
| `PainterPro/PaintRequest.cs` | `PaintMode`, `PaintRequest`, `PaintRequestMessage` (client to host) |
| `PainterPro/NetworkPaint.cs` | Validates and paints the network |
| `PainterPro/About/` | LaunchPad metadata, Workshop art, `bepinex` marker |
| `art/make_art.py` | Generates the Workshop art (render commands in its docstring) |
| `Stationeers.User.props` | Game path (tracked default) |
| `Deploy.User.props` | Machine-local save-data path (gitignored) |

```bash
dotnet build PainterPro
```

With `Deploy.User.props` setting `StationeersSaveDataDirectory`, the
`DeployLocalMod` target copies the DLL and `About/` files into
`mods/PainterPro`. A dedicated server needs the DLL in `mods/PainterPro/` and
`About.xml` in `mods/PainterPro/About/` (not the mod root), and **a restart**: a
running server keeps the old DLL in memory and keeps advertising the old version
to joining clients.

The empty `About/bepinex` marker is not checked by LaunchPad 1.2.1 (other mods load
without one); it is kept because it is harmless.

## Shipping a new version

1. Bump `Version` in `PainterPro/About/About.xml` and `PainterProPlugin.Version`.
2. Replace `<ChangeLog>` in `About.xml` (the Workshop change note, max 8000 chars).
3. `dotnet build PainterPro`, test in game.
4. In game: LaunchPad Workshop list, PainterPro, **Update**. If it says
   **Publish**, `<WorkshopHandle>` is missing and publishing would create a
   duplicate item.
5. GitHub release: zip `PainterPro/{PainterPro.dll, About/{About.xml, bepinex,
   thumb.png, Preview.png}}`, `gh release create vX.Y ...`, then download the
   asset URL to verify it.
6. Deploy to any dedicated server and restart it.

Editing the csproj changes the DLL hash even with identical source; compare
commits, not hashes, to answer "is this the same code".

## Gotchas (all found the hard way)

- **Never enable the Workshop copy and a local `mods/` copy at the same time.**
  Both load, the message registers twice (`ArgumentException ... same key ...
  PaintRequestMessage`) and the game fails to start. LaunchPad 1.2.1 skips its
  duplicate check while a mod pack is active. Keep a dev pack with the local copy
  and a play pack with the Workshop copy.
- **Networks are not single-cell.** `PipingLong` covers 3, 5 or 10 cells with one
  `Position`, and long (e.g. 10-unit) cables exist too. Anything computed from
  `Thing.Position` on the 0.5 grid is wrong for them; walk the graph instead.
  Include long pipes and long cables in every test.
- **Check grid/parity maths numerically before "fixing" it.** It was wrongly
  changed twice on reasoning alone. Saves are zip archives; `world.xml` has
  `WorldPosition` for every structure. Test on a long straight run: a short
  network with a tank and a corner looks broken when it is only sample size.
- **A Harmony prefix exception aborts the patched method.** On something central
  like `OnServer.SetCustomColor`, one bad line disables a game feature everywhere.
  If the mod seems to disable vanilla behaviour, look for an exception first.
- **`harmony.PatchAll` stops at the first failing patch** and silently skips the
  rest. Patch each class with `CreateClassProcessor(type).Patch()` in a try/catch.
- **Game updates break mods at the call site, not at load.** "Loaded fine" proves
  nothing; rebuild against the current game assembly first.
- **`ThingColorMessage` is never sent on a dedicated server** (only when
  `NetworkManager.IsClient`). Capture client identity in your own message.
- **`SprayGun.OnUseItem` never fires client-side**; the client validates and sends
  `AttackWithMessage`, the server executes. Intercept at `OnServer.AttackWith`.
- `ISprayer.DoSpray` is a static interface method and cannot be patched.
  `OnServer` is in the global namespace.
- On a dedicated server, runtime `Debug.Log` output is not in
  `BepInEx/LogOutput.log` (startup only); check the server tool's own log.
- LaunchPad `MonoBehaviour`/`ModBehaviour` entrypoints never get `OnLoaded`; use a
  BepInEx `[BepInPlugin]`.

Inspecting the game: a throwaway .NET console app using
`System.Reflection.MetadataLoadContext` over `rocketstation_Data/Managed` answers
"does this type/member still exist" quickly; ilspycmd decompiles. Keep output out of
the repo.

## Identity

ModID and GUID `net.jweisner.stationeers.PainterPro`. Published; do not change.

## Conventions

- Commit and push straight to `main`; no pull requests.
- No AI attribution trailers (`Co-Authored-By` and similar) in commits.
- Apache 2.0.
