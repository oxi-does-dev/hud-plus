"""HUD+ 5 in a running modded game: its row and buttons in Options > Mods, the
config file they write, the HUD drawn in the corners and turned off by the
command, the settings rail and its module and caption pages, the empty-module
modes, dragging the subtitles, the vanilla list hit test and the layout editor
opening as the mod's own screen."""
import json
import time
from game import Game, difference

CONFIG = "config/hud_plus.json"
TOP_LEFT, BOTTOM_CENTER = (0.0, 0.0, 0.3, 0.15), (0.3, 0.78, 0.7, 0.92)
# 1280x720 at GUI scale 2: the vanilla list starts at (4, 22 + 14) and each row
# is 13 GUI pixels tall.
VANILLA_ROW_X, VANILLA_ROW0_Y, VANILLA_ROW_H = 80, 36, 13
VANILLA_ROWS = ["Crosshair", "Hotbar", "Effect icons", "Boss bars", "XP / locator bar",
                "Health & hunger", "Item name", "Mount health", "Action bar", "Title",
                "Subtitles", "Scoreboard", "Chat", "Player list"]
# The settings panel is 640 GUI pixels wide at this scale; its rail starts at
# x=305 and the rows at x=402. The rows are 13 GUI pixels tall.
SETTINGS_ROW_X, SETTINGS_ROW0_Y, SETTINGS_ROW_H = 500, 24, 13
SETTINGS_TAB_X, SETTINGS_TAB0_Y, SETTINGS_TAB_H = 350, 24, 16
SETTINGS_TABS = ["General", "AppleSkin", "Effects", "Inventory", "Armour", "Captions",
                 "Coordinates", "Keys", "Info", "Health", "Held", "Vanilla HUD", "Tooltips"]


def cfg_now(g):
    return json.loads((g.home / CONFIG).read_text())


def run(ctl, resources, out):
    with Game(ctl, resources, out, {"options.txt": "guiScale:2\n"}) as g:
        results = {}
        g.run("options", "mods")
        assert "HUD+ 5: ON" in g.labels(), g.labels()
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

        # The settings screen is one panel on the right, with a rail of pages:
        # the world to its left keeps its brightness, and a click changes the
        # row under the pointer.
        before = g.shot("5-before-settings")
        g.run("key", "n", "tap")
        time.sleep(1)
        settings = g.shot("6-settings")
        results["settings_screen"] = g.run("status").get("screen")
        results["diff_outside_settings"] = round(difference(before, settings, (0.0, 0.0, 0.45, 1.0)), 1)
        assert results["settings_screen"] == "mod", results
        assert results["diff_outside_settings"] < 4, results

        # Captions have their own page: horizontal, vertical and scale act on
        # the subtitle box directly, without needing a sound to be playing.
        cap = SETTINGS_TABS.index("Captions")
        g.run("click-at", SETTINGS_TAB_X, SETTINGS_TAB0_Y + (cap + 0.5) * SETTINGS_TAB_H)
        time.sleep(0.4)
        for row in (1, 2, 3):
            g.run("click-at", SETTINGS_ROW_X, SETTINGS_ROW0_Y + (row + 0.5) * SETTINGS_ROW_H)
            time.sleep(0.15)
        time.sleep(0.5)
        cfg = cfg_now(g)
        subtitle = cfg["vanilla"]["elements"]["subtitle"]
        results["caption_settings"] = subtitle
        assert subtitle["x"] == 8 and subtitle["y"] == 8, subtitle
        assert abs(subtitle["scale"] - 1.05) < 0.001, subtitle
        g.shot("6b-captions")
        # Reset captions puts it back where the game draws it.
        g.run("click-at", SETTINGS_ROW_X, SETTINGS_ROW0_Y + 4.5 * SETTINGS_ROW_H)
        time.sleep(0.5)
        subtitle = cfg_now(g)["vanilla"]["elements"]["subtitle"]
        assert subtitle["x"] == 0 and subtitle["y"] == 0, subtitle
        assert abs(subtitle["scale"] - 1.0) < 0.001, subtitle

        # Back on General: the empty-module mode is a real two-state choice,
        # and the Theme row under the pointer is still the one that changes.
        general = SETTINGS_TABS.index("General")
        g.run("click-at", SETTINGS_TAB_X, SETTINGS_TAB0_Y + (general + 0.5) * SETTINGS_TAB_H)
        time.sleep(0.4)
        empty_row = 10
        g.run("click-at", SETTINGS_ROW_X, SETTINGS_ROW0_Y + (empty_row + 0.5) * SETTINGS_ROW_H)
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["empty_mode_full"] = cfg["empty_mode"]
        assert cfg["empty_mode"] == "always_full", cfg
        g.shot("6c-always-full")
        g.run("click-at", SETTINGS_ROW_X, SETTINGS_ROW0_Y + (empty_row + 0.5) * SETTINGS_ROW_H)
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["empty_mode_compact"] = cfg["empty_mode"]
        assert cfg["empty_mode"] == "compact", cfg
        g.run("click-at", SETTINGS_ROW_X, SETTINGS_ROW0_Y + 2.5 * SETTINGS_ROW_H)
        time.sleep(0.5)
        cfg = cfg_now(g)
        results["theme_after_row_click"] = cfg["theme"]
        assert cfg["theme"] != "dark", results
        g.run("scroll-at", SETTINGS_ROW_X, 200, -8)
        time.sleep(0.5)
        assert g.run("status").get("screen") == "mod", results
        g.run("key", "esc", "tap")
        time.sleep(1)
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
        print(json.dumps({"proof": "hud_plus", "ok": True, "settings": bool(settings),
                          "subtitle_row": bool(sub_row is not None), **results}, indent=2))
