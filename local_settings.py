# coding=utf-8
DISABLED_STOPS = {
    "1121601": {"name": "M P",
                "show_lines": ["Metro"]},
}

STOPS = {
    "1121602": {"name": "M E",
                "show_lines": ["Metro"]},
    "1113434": {"name": "Ratikat P",
                "show_lines": ["7B"]},
    "1113435": {"name": "Ratikat E",
                "show_lines": ["7A", "6", "6T"]},
    "1113131": {"name": "Sörnäinen",
                "show_lines": ["65A", "66A"]},
    "1121124": {"name": "Sörnäinen",
                "show_lines": ["64"]},
}

FETCHER_INTERVAL = 60

LINE_MAPS = {
    "6": "6(T)",
    "6T": "6(T)",
    "65A": "65A/66A",
    "66A": "65A/66A",
}

LINE_DETAILS = {
    "6(T)": {"minimum_time": 45, "type": "tram", "icon": "train"},
    "65A/66A": {"minimum_time": 300, "type": "bus", "icon": "bus"},
    "64": {"minimum_time": 360, "type": "bus", "icon": "bus"},
    "Metro": {"minimum_time": 360, "type": "metro", "icon": "train"},
    "7A": {"minimum_time": 45, "type": "tram", "icon": "train"},
    "7B": {"minimum_time": 75, "type": "tram", "icon": "train"},
}
