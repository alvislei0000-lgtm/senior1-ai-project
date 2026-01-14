from __future__ import annotations

from typing import Dict, TypedDict


class GameRequirement(TypedDict):
    vramByResolution: Dict[str, float]  # GB
    ram: float  # GB


# 只保留 25 款（對齊前端批次查詢用的熱門清單）
POPULAR_GAMES_25 = [
    "Minecraft",
    "Elden Ring",
    "Alan Wake 2",
    "Fortnite",
    "Escape from Tarkov",
    "Dragon's Dogma 2",
    "Cyberpunk 2077",
    "Counter-Strike 2",
    "Valorant",
    "Overwatch 2",
    "Apex Legends",
    "Halo Infinite",
    "Ready or Not",
    "PUBG: Battlegrounds",
    "Rust",
    "Assetto Corsa Competizione",
    "iRacing",
    "Cities: Skylines",
    "Starfield",
    "Forza Horizon 5",
    "Red Dead Redemption 2",
    "The Witcher 3",
    "Baldur's Gate 3",
    "Hogwarts Legacy",
    "Grand Theft Auto V",
]


def _v(v720: float, v1080: float, v1440: float, v4k: float) -> Dict[str, float]:
    return {
        "1280x720": float(v720),
        "1920x1080": float(v1080),
        "2560x1440": float(v1440),
        "3840x2160": float(v4k),
    }


# VRAM/RAM heuristic（不代表官方或實測；用於「是否可能 VRAM 不足」的提示）
GAME_REQUIREMENTS_25: Dict[str, GameRequirement] = {
    "Minecraft": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Elden Ring": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Alan Wake 2": {"vramByResolution": _v(6, 8, 10, 12), "ram": 16},
    "Fortnite": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
    "Escape from Tarkov": {"vramByResolution": _v(3, 4, 6, 8), "ram": 16},
    "Dragon's Dogma 2": {"vramByResolution": _v(6, 8, 10, 12), "ram": 16},
    "Cyberpunk 2077": {"vramByResolution": _v(6, 8, 10, 12), "ram": 16},
    "Counter-Strike 2": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
    "Valorant": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
    "Overwatch 2": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
    "Apex Legends": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
    "Halo Infinite": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Ready or Not": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "PUBG: Battlegrounds": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
    "Rust": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Assetto Corsa Competizione": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "iRacing": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Cities: Skylines": {"vramByResolution": _v(3, 4, 6, 8), "ram": 16},
    "Starfield": {"vramByResolution": _v(6, 8, 10, 12), "ram": 16},
    "Forza Horizon 5": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Red Dead Redemption 2": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "The Witcher 3": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Baldur's Gate 3": {"vramByResolution": _v(4, 6, 8, 10), "ram": 16},
    "Hogwarts Legacy": {"vramByResolution": _v(6, 8, 10, 12), "ram": 16},
    "Grand Theft Auto V": {"vramByResolution": _v(3, 4, 6, 8), "ram": 8},
}










