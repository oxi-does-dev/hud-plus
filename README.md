# HUD+ 6

HUD+ is a native Horizon HUD mod: one bundle that replaces a pile of separate
HUD mods and adds a drag-and-drop layout editor. Everything is configurable in
game; no files need editing by hand.

## What it draws

| Module | What it shows |
| --- | --- |
| AppleSkin | The original mod's look: golden saturation outlines over the hunger icons, a barely visible exhaustion checkerboard behind the bar, the food and saturation the held item would restore flashing on the same bar, plus optional numbers and an exhaustion readout above it |
| Effects | Status effects with names, amplifiers, remaining time (clock, seconds, ticks or both), sorting, grouping, an expiring-only filter and a warning colour; can hide vanilla's icons |
| Inventory | The whole inventory, the hotbar, armour and offhand, stack counts, durability bars or percentages, the selected slot, and a preview beside an open container |
| Armour | Each armour piece and its remaining durability, with per-piece names, percentages, bars and a low-durability warning |
| Coordinates | XYZ, facing and yaw, chunk, dimension and the same place in the other dimension (the Nether is an eighth) |
| Keystrokes | WASD, space, sneak, sprint, mouse buttons and CPS |
| Performance & time | FPS, frame time, 1% low, world clock and day, local time and date, speed, compass |
| Player vitals | Health, absorption, armour, food, air and experience as labelled rows with bars |
| Held items | The held and offhand item, stack counts, arrows and totems, with durability |
| Tooltips | Food and saturation on food items; durability, max stack and the item id while sneaking |
| Vanilla HUD | The game's own widgets — crosshair, hotbar, health and hunger, XP bar, effect icons, boss bars, item name, action bar, title, subtitles, scoreboard, chat, player list and mount health — each moved and scaled by HUD+ (the full-screen sleep overlay is not listed: there is nothing to move in it) |

## Views

Every module has four views: **Minimal**, **Compact**, **Standard** and
**Full**. `Standard` follows the module's own switches; the other three are
presets, so one row under `N` makes a module tiny, tidy or exhaustive without
touching a dozen options. A profile picks a view for all modules: Minimal
gives every module its Minimal view, PvP gives Compact, and the rest give
Standard.

| Module | Minimal | Compact | Full |
| --- | --- | --- | --- |
| AppleSkin | outlines only | outlines and food numbers | saturation, numbers, exhaustion, regeneration and the item preview |
| Effects | icons only, three rows | icons, names and time, six rows | names, amplifiers, ambient marks, every row, no limit |
| Inventory | hotbar only | hotbar and grid with stack counts | grid, armour, offhand, empty slots, counts and durability |
| Armour | icons only | icons and percentage | names, percentages, bars and the held item |
| Coordinates | XYZ only | XYZ and facing | chunk, dimension, Nether equivalent, yaw and two decimals |
| Keystrokes | WASD only | WASD and mouse | space, sneak, sprint, CPS and labels |
| Performance & time | FPS only | FPS and world clock | frame time, 1% low, real time, speed and compass |
| Player vitals | health only | health, food and bars | absorption, armour, air, XP and bars |
| Held items | name only | name and count | offhand, arrows, totems, counts and durability |

AppleSkin follows [squeek502/AppleSkin](https://github.com/squeek502/AppleSkin) (26.3):
its four saturation outlines from `icons.png` (public domain) sit on the vanilla
hunger bar, and holding food flashes the hunger and saturation it would restore.
A faint checkerboard is painted behind the hunger icons and gets a little
brighter as exhaustion climbs to 4; it is on in Standard and Full and off in
the two smaller views. Moving *Health & hunger* on the Vanilla page takes the
overlay with the bar.

### Empty modules

The *Empty modules* row on the General page decides what a module with nothing
to show does, for every module at once:

- **Compact** (default) hides the module. An empty inventory disappears
  completely instead of shrinking to a padded dot, and empty effects, armour,
  held-item and info modules leave no panel behind.
- **Always full** keeps each enabled module in place. The inventory keeps its
  full slot grid with the blank slots visible; text modules show one quiet
  placeholder (`No effects`, `No armour`, `Empty hand`, `No info fields`) so
  the layout does not jump around while the world changes.


All modules have an anchor (nine positions), an offset, a scale, a background
and a border, plus the four views above. Five profiles (Default, Minimal, PvP,
Builder, Streamer) and six themes (Dark, Light, Transparent, Neon, High
contrast, Amber) set everything at once.

## Using it

- `H` opens the editor on the HUD+ page: drag a module to move it, use the
  wheel over it to scale it, right-click to show or hide it, middle-click to
  cycle its anchor, the arrow keys to nudge it, `Space` to toggle it and `R` to
  reset the layout. The top bar has `HUD+`, `Vanilla` and `General` buttons;
  `Tab` walks the two pages, and `Esc` closes.
- `V` opens the same editor on the `Vanilla` page. Every layer of Minecraft's
  HUD is listed on the left and boxed on screen: drag a box or a row to move
  that widget, wheel over it to scale it around its pivot, right-click to put
  it back to vanilla, middle-click to reset it, `Space` to switch its control
  on or off and `R` to reset every widget. The real HUD stays visible while you
  edit, so what you see is what the game draws.
- There is no separate settings screen. Select a module and press `Enter`, or
  click the `Options` chip on it, and its options open in a small card beside
  the module. The card holds only that module's rows, plus `Enabled`, `View`,
  `Anchor`, `Scale`, `Background` and `Border`. Click outside the card (or
  press `Esc`/`Tab`) to close it without leaving the editor.
- `N` (or the `General` button) opens the General card at the top-left. It
  holds everything shared by the whole HUD: the master switch, profile, theme,
  opacity, text shadow, snap and grid, the layout and General hotkeys, hints,
  the *Empty modules* choice, *Move vanilla HUD*, the two tooltip switches,
  *Edit vanilla HUD*, the layout reset and *Reset everything*.
- Every row is a real control, not a line that happens to react. Switches show
  `ON`/`OFF` with a pill; numbers and choices show `< value >` arrows; buttons
  such as *Edit vanilla HUD* end with `>`. Click the arrows (or the row) to
  change a value, right-click a row to step it back, and `R` resets the focused
  row to its default. `Up`/`Down` move the focus, `Left`/`Right` change it,
  `Enter`/`Space` press it, `Page Up`/`Page Down` move a page at a time, and
  the footer explains the highlighted row. *Reset layout* and *Reset
  everything* ask for a second click before they wipe anything.
- Subtitles are moved on the `Vanilla` page: select *Subtitles* in the list or
  click its box, then drag it, wheel to scale it, or use the arrow keys. `R`
  puts the whole vanilla HUD back.
- General also has the **Empty modules** choice (`Always full` or `Compact`,
  see above) and turns the vanilla widget control on or off.
- `/hudplus` shows the command help. `/hudplus on|off`, `layout`, `settings`,
  `reset`, `profile <name>` and `theme <name>` also work.
- Options > Mods lists HUD+ and has buttons for on/off, theme, profile and a
  layout reset.

The configuration is `config/hud_plus.json` in the game directory. Changes are
saved as they are made.

## On servers

HUD+ draws only. A server sees exactly the packets of a plain Horizon client
with the same settings, so there is nothing for it to detect or to ban:

- The modules have no network code: no packets, no connection, no sockets, no
  second process. `check_client_only.py` scans every source for those calls and
  fails the build if one ever appears; CI runs it for this mod, and so can you:
  `python3 check_client_only.py`.
- The mod is compiled into the client binary. It is not in the `mods/` folder
  and has no jar or `.hmod`, so a plugin that scans files has nothing to find.
- `minecraft:brand` is the one a plain Horizon client sends ("vanilla" to
  other servers, "horizon" on a Horizon server after it identifies itself), and
  Horizon's `horizon:mod_list` carries content mods (`side = "both"`) only, so
  a client-only HUD is never named to the server.
- It never acts for the player: no movement, attack, use, drop or selection
  calls, no key injection and no macro. Keys are only read, to open the mod's
  own screens and to draw the keystrokes module.
- `/hudplus` is a client command: the game runs it and does not send it.

That covers Horizon's own anticheat (which judges the moves, attacks and packet
timing a client sends, all untouched) and server-side anticheats that look at
the same traffic. Some servers also restrict what a HUD may show by their rules
— coordinates, for one. Every module has a switch under `N`, and the master
switch on the first row turns the whole HUD off, without leaving the world.

## Packet audit

The "draws only" claim is checked on the wire. `tools/packet_audit.py` starts a
fresh dedicated server behind a decoding proxy, joins it first with a stock
Horizon client and then with the HUD+ build, runs one scripted session (walk,
sprint, jump, sneak, inventory clicks, chat, a command, dropping an item and
two attacks), and records every packet in both directions. `compare` requires
the handshake, login, configuration, `client_information`, `custom_payload`,
every action packet and the 20 Hz tick rate to match; `audit` adds the
anticheat's view (timer, horizontal speed, falls, attacks covered by swings,
one target per tick, no mod id in the traffic). Movement packet counts and
flag mixes are reported, not gated: a key change on a frame boundary moves
them by a packet or two in either client.

It needs a Horizon build and a prepared server directory (`server.toml` with
`whitelist = false`); a capture deletes that directory's world and makes a
new one.

```sh
python3 tools/packet_audit.py capture \
  --client /path/to/horizon-client.orig \
  --server /path/to/horizon-server --ctl /path/to/horizon-ctl \
  --ids /path/to/horizon/crates/horizon-protocol/src/ids.rs \
  --server-dir /path/to/server --out stock.jsonl
python3 tools/packet_audit.py capture ... \
  --client /path/to/horizon-client --out hud.jsonl
python3 tools/packet_audit.py compare stock.jsonl hud.jsonl --json report.json
python3 tools/packet_audit.py audit hud.jsonl
python3 tools/packet_audit.py matrix --stock stock*.jsonl --hud hud*.jsonl
```

## Responsibility and support

HUD+ is a free, unofficial, client-side mod, provided under the MIT licence
**as is, without warranty of any kind**. It changes only what you see in your
own client: it sends nothing, keeps no telemetry and has no server component,
so it cannot affect other players or a server's data. Using it is at your own
risk, and every player is responsible for checking that a server's rules allow
the modules they turn on (coordinates and keystroke displays are the usual
ones). The author maintains it in their own time, offers no support guarantee,
and is not liable for bans, lost items or other consequences of use; the
licence says the same in legal terms. Bug reports and pull requests are
welcome in the source repository.

## Building

The bundle is a `horizon-mixins` native mod:

```sh
horizon-mixins apply \
  --workspace /path/to/horizon \
  --mods /path/to/hud-plus/mixins \
  --out /path/to/staged-horizon
cargo build --release -p horizon-client --bin horizon-client
```

`compatibility.json` names the Horizon revision the mod was written against
and the native hook API it needs (`139`: the HUD layer hooks). The launcher can
build it on any Horizon whose `NATIVE_HOOKS_API` is at least that, together
with other native mods; the revision is only the one it was tested on.
