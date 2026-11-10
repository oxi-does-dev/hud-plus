"""HUD+ 6 in a running modded game: its row and buttons in Options > Mods, the
config file they write, the HUD drawn in the corners and turned off by the
command, the one editor screen with its General and module options cards, the
empty-module modes, dragging the subtitles, the vanilla list hit test and the
editor opening as the mod's own screen."""
import json
import time
from game import Game, difference

CONFIG = "config/hud_plus.json"
VERSION = "6"
TOP_LEFT, BOTTOM_CENTER = (0.0, 0.0, 0.3, 0.15), (0.3, 0.78, 0.7, 0.92)
# 1280x720 at GUI scale 2: the vanilla list starts at (4, 22 + 14) and each row
# is 13 GUI pixels tall.
VANILLA_ROW_X, VANILLA_ROW0_Y, VANILLA_ROW_H = 80, 36, 13
VANILLA_ROWS = ["Crosshair", "Hotbar", "Effect icons", "Boss bars", "XP / locator bar",
                "Health & hunger", "Item name", "Mount health", "Action bar", "Title",
                "Subtitles", "Scoreboard", "Chat", "Player list"]
# The General card sits at the top-left: 232 GUI pixels wide, 20-pixel header,
# then 20-pixel rows. At GUI scale 2 the window is 640x360 GUI pixels.
CARD_X, CARD_Y, CARD_HEADER, CARD_ROW_H = 6, 24, 20, 20
GENERAL_ROW_X = 120
# General rows, 0-based, in drawing order.
GENERAL_ROWS = ["HUD enabled", "Profile", "Theme", "Opacity", "Text shadow",
                "Snap to grid", "Grid", "Layout hotkey", "Settings hotkey",
                "Show hints", "Empty modules", "Move vanilla HUD",
                "Food values in tooltips", "Sneak details in tooltips",
                "Edit vanilla HUD", "Reset layout", "Reset everything", "Close editor"]
MODULE_KEYS = ["apple_skin", "effects", "inventory", "armor", "coords", "keys",
               "info", "health", "held"]


def general_row(index):
    return GENERAL_ROW_X, CARD_Y + CARD_HEADER + (index + 0.5) * CARD_ROW_H


def cfg_now(g):
    return json.loads((g.home / CONFIG).read_text())


def run(ctl, resources, out):
    with Game(ctl, resources, out, {"options.txt": "guiScale:2\n"}) as g:
        results = {}
        g.run("options", "mods")
        assert f"HUD+ {VERSION}: ON" in g.labels(), g.labels()
        g.run("click", g.ids()["Settings"])
        page = g.labels()
        assert page[:4] == ["HUD: on", "Theme: Dark", "Profile: Default", "Reset layout"], page
        g.shot("1-options")
        g.run("click", g.ids()["HUD: on"])
        cfg = cfg_now(g)
        results["enabled_after_click"] = cfg["enabled"]
        g.play()
        # The default profile names a layout but leaves every module off; a
        # builder layout gives the test something to see in both corners.
        g.run("chat", "/hudplus profile builder")
        g.run("command", "tp @s ~ ~ ~ 0 10")
        time.sleep(2)
        off = g.shot("2-hud-off")

        g.run("chat", "/hudplus on")
        time.sleep(2)
        on = g.shot("3-hud-on")
        results["diff_top_left"] = round(difference(off, on, TOP_LEFT), 1)
        results["diff_bottom_center"] = round(difference(off, on, BOTTOM_CENTER), 1)
        assert results["diff_top_left"] > 4 or results["diff_bottom_center"] > 4, results

        g.run("chat", "/hudplus theme neon")
        time.sleep(2)
        neon = g.shot("4-neon")
        results["diff_neon"] = round(difference(on, neon, TOP_LEFT), 1)
        cfg = cfg_now(g)
        results["theme"] = cfg["theme"]
        assert cfg["theme"] == "neon", results
        g.run("chat", "/hudplus theme dark")

        # The editor is one screen. N opens it with the General card at the
        # top-left; there is no separate settings screen any more.
        before = g.shot("5-before-editor")
        g.run("key", "n", "tap")
        time.sleep(1)
        card = g.shot("6-general-card")
        results["editor_screen"] = g.run("status").get("screen")
        assert results["editor_screen"] == "mod", results
        # The card is painted over the dimmed world: the left column changes
        # while the game stays behind it.
        results["diff_general_card"] = round(difference(before, card, (0.0, 0.0, 0.4, 1.0)), 1)
        assert results["diff_general_card"] > 4, results

        # General rows are real controls: Empty modules flips between the two
        # modes, and the Theme row under the pointer still changes the theme.
        empty_row = GENERAL_ROWS.index("Empty modules")
        g.run("click-at", *general_row(empty_row))
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["empty_mode_full"] = cfg["empty_mode"]
        assert cfg["empty_mode"] == "always_full", cfg
        g.shot("6b-always-full")
        g.run("click-at", *general_row(empty_row))
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["empty_mode_compact"] = cfg["empty_mode"]
        assert cfg["empty_mode"] == "compact", cfg
        g.run("click-at", *general_row(GENERAL_ROWS.index("Theme")))
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["theme_after_row_click"] = cfg["theme"]
        assert cfg["theme"] != "dark", results
        # The wheel scrolls the card's rows without leaving the editor.
        g.run("scroll-at", GENERAL_ROW_X, 200, -8)
        time.sleep(0.5)
        assert g.run("status").get("screen") == "mod", results

        # Enter opens the selected module's own card. Its rows start at
        # Enabled, View, Anchor: Down twice then Right cycles the anchor.
        g.run("key", "esc", "tap")
        time.sleep(0.4)
        cfg = cfg_now(g)
        module = next(k for k in MODULE_KEYS if cfg[k]["module"]["enabled"])
        anchor_before = cfg[module]["module"]["anchor"]
        g.run("key", "enter", "tap")
        time.sleep(0.5)
        g.run("key", "down", "tap")
        g.run("key", "down", "tap")
        g.run("key", "right", "tap")
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["module_card"] = module
        results["module_anchor"] = cfg[module]["module"]["anchor"]
        assert cfg[module]["module"]["anchor"] != anchor_before, (anchor_before, cfg[module])
        g.shot("6c-module-card")
        # Esc leaves the card first, then the editor.
        g.run("key", "esc", "tap")
        time.sleep(0.4)
        g.run("key", "esc", "tap")
        time.sleep(0.8)
        g.run("chat", "/hudplus theme dark")

        # The vanilla list row under the pointer is the one selected: the
        # Subtitles row moves Subtitles and leaves Scoreboard alone.
        g.run("key", "v", "tap")
        time.sleep(1)
        sub_row = VANILLA_ROWS.index("Subtitles")
        g.run("click-at", VANILLA_ROW_X, VANILLA_ROW0_Y + (sub_row + 0.5) * VANILLA_ROW_H)
        g.run("key", "right", "tap")
        g.run("key", "right", "tap")
        time.sleep(0.5)
        cfg = cfg_now(g)
        subtitle = cfg["vanilla"]["elements"]["subtitle"]
        scoreboard = cfg["vanilla"]["elements"]["scoreboard"]
        results["subtitle_x"] = subtitle["x"]
        results["scoreboard_x"] = scoreboard["x"]
        assert subtitle["x"] == 16, cfg["vanilla"]
        assert scoreboard["x"] == 0 and scoreboard["y"] == 0, cfg["vanilla"]
        g.shot("7-subtitles-selected")
        # Dragging the box itself moves the same widget, not only the arrows.
        g.run("drag-at", 450, 325, 490, 325)
        time.sleep(0.5)
        dragged = cfg_now(g)["vanilla"]["elements"]["subtitle"]
        results["subtitle_drag_x"] = dragged["x"]
        assert dragged["x"] != subtitle["x"], (subtitle, dragged)
        g.run("key", "r", "tap")
        time.sleep(0.5)
        cfg = cfg_now(g)
        assert cfg["vanilla"]["elements"]["subtitle"]["x"] == 0, cfg["vanilla"]

        # The editor and the rest of the vanilla page still work.
        g.run("key", "esc", "tap")
        time.sleep(1)
        g.run("key", "h", "tap")
        time.sleep(1)
        g.shot("8-mods-page")
        assert g.run("status").get("screen") == "mod", results
        g.run("key", "tab", "tap")
        time.sleep(1)
        vanilla = g.shot("9-vanilla-page")
        cfg = cfg_now(g)
        results["vanilla_enabled"] = cfg["vanilla"]["enabled"]
        hotbar_row = VANILLA_ROWS.index("Hotbar")
        g.run("click-at", VANILLA_ROW_X, VANILLA_ROW0_Y + (hotbar_row + 0.5) * VANILLA_ROW_H)
        g.run("key", "right", "tap")
        g.run("key", "right", "tap")
        time.sleep(1)
        moved = g.shot("10-vanilla-moved")
        results["diff_vanilla"] = round(difference(vanilla, moved, (0.2, 0.75, 0.8, 1.0)), 1)
        cfg = cfg_now(g)
        results["hotbar_x"] = cfg["vanilla"]["elements"]["hotbar"]["x"]
        assert results["hotbar_x"] != 0, results
        g.run("key", "r", "tap")
        time.sleep(1)
        cfg = cfg_now(g)
        assert cfg["vanilla"]["elements"]["hotbar"]["x"] == 0, cfg["vanilla"]
        g.run("key", "esc", "tap")
        time.sleep(1)
        results["screen_after_escape"] = g.run("status").get("screen")
        assert results["screen_after_escape"] == "playing", results
        print(json.dumps({"proof": "hud_plus", "ok": True, "card": bool(card),
                          "subtitle_row": bool(sub_row is not None), **results}, indent=2))
