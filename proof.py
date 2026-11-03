"""HUD+ in a running modded game: its row and buttons in Options > Mods, the
config file they write, the HUD drawn in the corners and turned off by the
command, and the layout editor opening as the mod's own screen."""
import json
import time
from game import Game, difference

CONFIG = "config/hud_plus.json"
TOP_LEFT, BOTTOM_CENTER = (0.0, 0.0, 0.3, 0.15), (0.3, 0.78, 0.7, 0.92)


def run(ctl, resources, out):
    with Game(ctl, resources, out) as g:
        results = {}
        g.run("options", "mods")
        assert "HUD+ 3: ON" in g.labels(), g.labels()
        g.run("click", g.ids()["Settings"])
        page = g.labels()
        assert page[:4] == ["HUD: on", "Theme: Dark", "Profile: Default", "Reset layout"], page
        g.shot("1-options")
        g.run("click", g.ids()["HUD: on"])
        cfg = json.loads((g.home / CONFIG).read_text())
        results["enabled_after_click"] = cfg["enabled"]
        g.play()
        g.run("command", "tp @s ~ ~ ~ 0 10")
        time.sleep(2)
        off = g.shot("2-hud-off")

        g.run("command", "hudplus on")
        time.sleep(2)
        on = g.shot("3-hud-on")
        results["diff_top_left"] = round(difference(off, on, TOP_LEFT), 1)
        results["diff_bottom_center"] = round(difference(off, on, BOTTOM_CENTER), 1)
        assert results["diff_top_left"] > 4 or results["diff_bottom_center"] > 4, results

        g.run("command", "hudplus theme neon")
        time.sleep(2)
        neon = g.shot("4-neon")
        results["diff_neon"] = round(difference(on, neon, TOP_LEFT), 1)
        cfg = json.loads((g.home / CONFIG).read_text())
        results["theme"] = cfg["theme"]
        assert cfg["theme"] == "neon", results

        g.run("command", "hudplus layout")
        time.sleep(1)
        editor = g.shot("5-editor")
        results["screen"] = g.run("status").get("screen")
        results["editor_is_a_mod_screen"] = results["screen"] == "mod"

        g.run("key", "tab", "tap")
        time.sleep(1)
        vanilla = g.shot("6-vanilla-page")
        cfg = json.loads((g.home / CONFIG).read_text())
        results["vanilla_enabled"] = cfg["vanilla"]["enabled"]
        g.run("key", "right", "tap")
        g.run("key", "right", "tap")
        time.sleep(1)
        moved = g.shot("7-vanilla-moved")
        results["diff_vanilla"] = round(difference(vanilla, moved, (0.2, 0.75, 0.8, 1.0)), 1)
        cfg = json.loads((g.home / CONFIG).read_text())
        results["hotbar_x"] = cfg["vanilla"]["elements"]["hotbar"]["x"]
        assert results["hotbar_x"] != 0, results
        g.run("key", "r", "tap")
        time.sleep(1)
        cfg = json.loads((g.home / CONFIG).read_text())
        assert cfg["vanilla"]["elements"]["hotbar"]["x"] == 0, cfg["vanilla"]
        g.run("key", "esc", "tap")
        time.sleep(1)
        results["screen_after_escape"] = g.run("status").get("screen")
        assert results["editor_is_a_mod_screen"], results
        assert results["screen_after_escape"] == "playing", results
        print(json.dumps({"proof": "hud_plus", "ok": True, "editor": bool(editor), **results}, indent=2))
