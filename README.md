# HUD+ 3

HUD+ is a native Horizon HUD mod: one bundle that replaces a pile of separate
HUD mods and adds a drag-and-drop layout editor. Everything is configurable in
game; no files need editing by hand.

## What it draws

| Module | What it shows |
| --- | --- |
| AppleSkin | The original mod's look: golden saturation outlines over the hunger icons, the food and saturation the held item would restore flashing on the same bar, plus optional numbers and an exhaustion readout above it |
| Effects | Status effects with names, amplifiers, remaining time (clock, seconds, ticks or both), sorting, grouping, an expiring-only filter and a warning colour; can hide vanilla's icons |
| Inventory | The whole inventory, the hotbar, armour and offhand, stack counts, durability bars or percentages, the selected slot, and a preview beside an open container |
| Armour | Each armour piece and its remaining durability, with per-piece names, percentages, bars and a low-durability warning |
| Coordinates | XYZ, facing and yaw, chunk, dimension and the same place in the other dimension (the Nether is an eighth) |
| Keystrokes | WASD, space, sneak, sprint, mouse buttons and CPS |
| Performance & time | FPS, frame time, 1% low, world clock and day, local time and date, speed, compass |
| Player vitals | Health, absorption, armour, food, air and experience as labelled rows with bars |
| Held items | The held and offhand item, stack counts, arrows and totems, with durability |
| Tooltips | Food and saturation on food items; durability, max stack and the item id while sneaking |
| Vanilla HUD | The game's own widgets — crosshair, hotbar, health and hunger, XP bar, effect icons, boss bars, item name, action bar, title, subtitles, scoreboard, chat, player list, mount health and the sleep overlay — each moved and scaled by HUD+ |

AppleSkin follows [squeek502/AppleSkin](https://github.com/squeek502/AppleSkin) (26.3):
its four saturation outlines from `icons.png` (public domain) sit on the vanilla
hunger bar, and holding food flashes the hunger and saturation it would restore.
Moving *Health & hunger* on the Vanilla page takes the overlay with the bar.


All modules have an anchor (nine positions), an offset, a scale, a background
and a border. Five profiles (Default, Minimal, PvP, Builder, Streamer) and six
themes (Dark, Light, Transparent, Neon, High contrast, Amber) set everything at
once.

## Using it

- `H` opens the layout editor on the HUD+ page: drag a module to move it, use
  the wheel over it to scale it, right-click to show or hide it, middle-click
  to cycle its anchor, the arrow keys to nudge it, `Space` to toggle it and
  `R` to reset the layout. `Tab` turns the page to `Vanilla`, another `Tab`
  opens settings; `Esc` closes.
- `V` (or Settings > Vanilla HUD > Edit vanilla layout) opens the same editor
  on the `Vanilla` page. Every layer of Minecraft's HUD is listed on the left
  and boxed on screen: drag a box or a row to move that widget, wheel over it
  to scale it around its pivot, right-click to put it back to vanilla, middle-
  click to reset it, `Space` to switch its control on or off and `R` to reset
  every widget. The real HUD stays visible while you edit, so what you see is
  what the game draws.
- `N` opens settings: a scrollable list of every option, with sections. Click a
  row to change it; right-click goes back. The first row is the master switch,
  so the whole HUD can be turned off without leaving the world. Its `Vanilla
  HUD` section turns the widget control on or off and opens the vanilla page.
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
