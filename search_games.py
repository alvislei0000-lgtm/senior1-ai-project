#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Google搜索获取热门3A和FPS游戏信息并添加到游戏列表
"""

import json
import os
import re
import sys
from google_programmable_search import google_search

# Known popular games to look for
POPULAR_GAMES_LIST = [
    # 3A Games - AAA Titles
    "Baldur's Gate 3", "Alan Wake 2", "Marvel's Spider-Man 2", "Final Fantasy VII Rebirth",
    "Dragon's Dogma 2", "Starfield", "The Elder Scrolls VI", "Cyberpunk 2077",
    "Hogwarts Legacy", "Assassin's Creed Mirage", "Avatar: Frontiers of Pandora",
    "Prince of Persia: The Lost Crown", "Lies of P", "Throne and Liberty",
    "Warhammer 40,000: Space Marine 2", "Company of Heroes 3", "Expeditions: A Mudrunner Game",
    "Concord", "Sword of the Sea", "Once Human", "Greyzone Warfare",
    "The Witcher 4", "Kingdom Come: Deliverance 2", "Mafia: Definitive Edition",
    "Mafia IV", "Watch Dogs: Legion", "Dying Light 3", "Mirror's Edge Catalyst",
    "Deus Ex: Mankind Divided", "Prey", "System Shock", "The Callisto Protocol",
    "Dead Space Remake", "Resident Evil 4 Remake", "Resident Evil 2 Remake",
    "Silent Hill 2 Remake", "The Last of Us Part II", "Horizon Forbidden West",
    "Ghost of Tsushima Director's Cut", "Ratchet & Clank: Rift Apart",
    "Spider-Man: Miles Morales", "Gran Turismo 7", "Forza Motorsport",
    "F1 2023", "Dirt Rally 2.0", "WRC Generations", "Project Cars 3",
    "Assetto Corsa Competizione", "iRacing", "rFactor 2",

    # FPS Games
    "Counter-Strike 2", "CS2", "Valorant", "Apex Legends", "Overwatch 2",
    "Call of Duty: Black Ops 6", "Rainbow Six Siege", "Destiny 2", "Team Fortress 2",
    "Paladins", "SMITE", "Warframe", "Halo Infinite", "Battlefield 2042",
    "Battlefield V", "Call of Duty: Modern Warfare III", "Call of Duty: Warzone",
    "Fortnite", "PUBG: Battlegrounds", "Escape from Tarkov", "Hunt: Showdown",
    "Ready or Not", "Zero Hour", "Hell Let Loose", "Post Scriptum", "Insurgency: Sandstorm",
    "Squad", "Ground Branch", "Arma Reforger", "Project Zomboid", "Miscreated",
    "SCUM", "The Forest", "Rust", "ARK: Survival Evolved", "7 Days to Die",
    "DayZ", "Unturned", "H1Z1", "PlayerUnknown's Battlegrounds",
    "Call of Duty: Vanguard", "Call of Duty: WWII", "Battlefield 1", "Battlefield 4",
    "Titanfall 2", "Doom Eternal", "Doom 2016", "Wolfenstein II: The New Colossus",
    "Metro Exodus", "Metro: Last Light Redux", "S.T.A.L.K.E.R. 2: Heart of Chornobyl",
    "Atomic Heart", "Chernobylite", "The Long Dark", "Frostpunk", "This War of Mine",

    # Additional popular games
    "Minecraft", "Roblox", "Among Us", "Fall Guys", "Rocket League",
    "Garry's Mod", "Portal 2", "Half-Life: Alyx", "Beat Saber", "The Sims 4",
    "Cities: Skylines", "Euro Truck Simulator 2", "American Truck Simulator",
    "Farming Simulator 22", "Stardew Valley", "Don't Starve Together",
    "Risk of Rain 2", "Valheim", "Deep Rock Galactic", "Noita", "Hades",
    "Loop Hero", "Hollow Knight", "Celeste", "Ori and the Will of the Wisps",
    "Dead Cells", "Enter the Gungeon", "Monster Hunter: World", "Monster Hunter Rise",
    "Monster Hunter: Iceborne", "Dark Souls III", "Bloodborne", "Sekiro: Shadows Die Twice",
    "Elden Ring", "Demon's Souls Remake", "Nioh 2", "Wo Long: Fallen Dynasty",
    "Divinity: Original Sin 2", "Pillars of Eternity II: Deadfire",
    "Planescape: Torment Enhanced", "Icewind Dale: Enhanced Edition",
    "Neverwinter Nights: Enhanced Edition", "Tyranny", "Wasteland 3",
    "Fallout: New Vegas", "Fallout 4", "Fallout 76", "The Outer Worlds", "Outer Wilds",
    "Subnautica", "Subnautica: Below Zero", "No Man's Sky", "Elite Dangerous",
    "Star Citizen", "EVE Online", "World of Warcraft", "The Elder Scrolls V: Skyrim",
    "The Elder Scrolls Online", "Morrowind", "Oblivion", "Dragon Age: Origins",
    "Dragon Age II", "Dragon Age: Inquisition", "Mass Effect Legendary Edition",
    "Mass Effect 2", "Mass Effect 3", "Kingdoms of Amalur: Re-Reckoning"
]

def extract_game_info_from_search_results(results, category="3a"):
    """
    Extract game information from search results
    """
    games = []

    for result in results:
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        full_text = (title + " " + snippet).lower()

        # Look for known games in the search results
        for known_game in POPULAR_GAMES_LIST:
            if known_game.lower() in full_text:
                if known_game not in [g['name'] for g in games]:
                    # Determine VRAM requirements based on game type
                    vram_720p = 4  # Default for 3A games
                    vram_1080p = 6
                    vram_1440p = 8
                    vram_4k = 10
                    ram = 16

                    # Higher requirements for demanding games
                    demanding_games = ["Baldur's Gate 3", "Alan Wake 2", "Marvel's Spider-Man 2",
                                     "Final Fantasy VII Rebirth", "Dragon's Dogma 2", "Starfield",
                                     "Cyberpunk 2077", "The Elder Scrolls VI", "Avatar: Frontiers of Pandora"]

                    if known_game in demanding_games:
                        vram_720p = 6
                        vram_1080p = 8
                        vram_1440p = 10
                        vram_4k = 12

                    # FPS games typically have lower requirements
                    fps_games = ["Counter-Strike 2", "CS2", "Valorant", "Apex Legends", "Overwatch 2",
                               "Rainbow Six Siege", "Team Fortress 2", "Paladins", "SMITE",
                               "Warframe", "Fortnite", "PUBG: Battlegrounds", "Escape from Tarkov"]

                    if known_game in fps_games:
                        vram_720p = 3
                        vram_1080p = 4
                        vram_1440p = 6
                        vram_4k = 8
                        ram = 8

                    # Indie games with lower requirements
                    indie_games = ["Stardew Valley", "Don't Starve Together", "Hades", "Loop Hero",
                                 "Hollow Knight", "Celeste", "Ori and the Will of the Wisps"]

                    if known_game in indie_games:
                        vram_720p = 2
                        vram_1080p = 3
                        vram_1440p = 4
                        vram_4k = 6
                        ram = 8

                    game_info = {
                        "name": known_game,
                        "vramByResolution": {
                            '1280x720': vram_720p,
                            '1920x1080': vram_1080p,
                            '2560x1440': vram_1440p,
                            '3840x2160': vram_4k
                        },
                        "ram": ram
                    }

                    games.append(game_info)
                    break  # Found this game, move to next result

    return games

def search_popular_games():
    """
    Search for popular 3A and FPS games
    """
    print("Searching for popular 3A and FPS games...")

    # Search queries for different types of games
    queries = [
        # 3A Games
        "popular AAA games 2024 system requirements",
        "best selling 3A games 2024 PC",
        "top rated action adventure games 2024",
        "popular RPG games 2024 system requirements",
        "upcoming AAA games 2024 2025",
        "best graphics games 2024 VRAM requirements",
        "most demanding PC games 2024",
        "high budget games 2024 requirements",
        "epic games store best games 2024",
        "steam top sellers 2024",

        # FPS Games
        "popular FPS games 2024 system requirements",
        "best competitive shooters 2024",
        "top rated battle royale games 2024",
        "popular multiplayer FPS games 2024",
        "CS2 Valorant system requirements",
        "Apex Legends Overwatch 2 requirements",
        "best tactical shooters 2024",
        "popular esports games 2024",
        "top FPS games steam charts",
        "most played FPS games",

        # Racing and Sports Games
        "popular racing games 2024 PC",
        "best sports games 2024 system requirements",
        "top racing simulators 2024",
        "popular driving games 2024",

        # Indie and Other Games
        "popular indie games 2024",
        "best survival games 2024",
        "top simulation games 2024",
        "popular strategy games 2024",
        "best horror games 2024 PC",

        # Additional popular games
        "popular PC games 2024 gaming requirements",
        "best selling games 2024 system specs",
        "high graphics games 2024 VRAM usage",
        "most popular games steam 2024",
        "top concurrent players steam games",
        "best rated games metacritic 2024"
    ]

    all_games = []

    for query in queries:
        print(f"Searching: {query}")
        try:
            results = google_search(query, "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU", "034784ab1b1404dc2", num=8)
            if results:
                games = extract_game_info_from_search_results(results)
                all_games.extend(games)
                print(f"Found {len(games)} potential game entries")
            else:
                print("No search results")
        except Exception as e:
            print(f"Search failed: {e}")
        print()

    # Remove duplicates
    unique_games = []
    seen_names = set()
    for game in all_games:
        if game['name'] not in seen_names:
            unique_games.append(game)
            seen_names.add(game['name'])

    return unique_games

def clean_invalid_games(file_path="frontend/src/data/games.ts"):
    """
    Remove invalid game entries from the games.ts file
    """
    # Read the current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the POPULAR_GAMES array
    start_pattern = r'export const POPULAR_GAMES: GameRequirements\[\] = \['
    end_pattern = r'\]'

    start_match = re.search(start_pattern, content)
    if not start_match:
        print("Could not find POPULAR_GAMES array in file")
        return

    start_pos = start_match.end()
    end_pos = content.rfind(']', start_pos)

    if end_pos == -1:
        print("Could not find end of POPULAR_GAMES array")
        return

    # Extract existing games
    existing_games_text = content[start_pos:end_pos]

    # Split into individual game objects
    games = []
    current_game = ""
    brace_count = 0
    lines = existing_games_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('{'):
            current_game = ""
            brace_count = 1
        if current_game is not None:
            current_game += line + "\n"
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and current_game.strip():
                games.append(current_game.strip())
                current_game = None

    # Filter out invalid games (those that don't look like real game names)
    valid_games = []
    invalid_patterns = [
        r'^\d{1,2}\/\d{1,2}$',  # Dates like "Apr 6", "Jul 14"
        r'^[A-Z][a-z]{2} \d{1,2}$',  # "Jul 3", "Sep 5"
        r'^What ',  # Questions
        r'^System Requirements',  # System requirements titles
        r'^Best ',  # "Best selling", "Best action"
        r'^Top ',  # "Top 10", "Top rated"
        r'^List of',  # Lists
        r'Wikipedia$',  # Wikipedia pages
        r'^The ',  # Generic titles
        r'Outlet$',  # Shopping terms
        r'^RPG M$',  # Incomplete
        r'^AAA G$',  # Incomplete
        r'^PC B$',  # Incomplete
        r'^VRAM A$',  # Incomplete
        r'^FPS Multi$',  # Incomplete
    ]

    for game_text in games:
        name_match = re.search(r'name:\s*["\']([^"\']+)["\']', game_text)
        if name_match:
            game_name = name_match.group(1)
            is_valid = True

            # Check against invalid patterns
            for pattern in invalid_patterns:
                if re.search(pattern, game_name):
                    is_valid = False
                    break

            # Additional checks for obviously invalid names
            if len(game_name) < 3 or len(game_name) > 50:
                is_valid = False
            elif not any(c.isalpha() for c in game_name):  # No letters
                is_valid = False
            elif game_name.count(' ') > 5:  # Too many spaces
                is_valid = False

            if is_valid:
                valid_games.append(game_text)
            else:
                print(f"Removing invalid game: {game_name}")

    # Reconstruct the games array
    new_games_text = "[\n"
    for game in valid_games:
        new_games_text += "  " + game + ",\n"
    new_games_text = new_games_text.rstrip(',\n') + "\n]"

    # Replace the old array with the cleaned one
    new_content = content[:start_pos] + new_games_text + content[end_pos:]

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Cleaned games list. Removed {len(games) - len(valid_games)} invalid entries.")

def add_games_to_games_file(new_games, file_path="frontend/src/data/games.ts"):
    """
    Add new games to the games.ts file
    """
    # First clean invalid entries
    clean_invalid_games(file_path)

    # Read the current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse existing games
    # Find the POPULAR_GAMES array
    start_pattern = r'export const POPULAR_GAMES: GameRequirements\[\] = \['
    end_pattern = r'\]'

    start_match = re.search(start_pattern, content)
    if not start_match:
        print("Could not find POPULAR_GAMES array in file")
        return

    start_pos = start_match.end()
    end_pos = content.rfind(']', start_pos)

    if end_pos == -1:
        print("Could not find end of POPULAR_GAMES array")
        return

    # Extract existing games
    existing_games_text = content[start_pos:end_pos]
    existing_games = []

    # Parse existing games (simple approach - split by lines and find game objects)
    lines = existing_games_text.strip().split('\n')
    current_game = None
    brace_count = 0

    for line in lines:
        line = line.strip()
        if line.startswith('{'):
            current_game = ""
            brace_count = 1
        if current_game is not None:
            current_game += line + "\n"
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and current_game.strip():
                existing_games.append(current_game.strip())
                current_game = None

    # Convert to game objects for duplicate checking
    existing_game_names = set()
    for game_text in existing_games:
        name_match = re.search(r'name:\s*["\']([^"\']+)["\']', game_text)
        if name_match:
            existing_game_names.add(name_match.group(1))

    # Filter new games to avoid duplicates
    games_to_add = []
    for new_game in new_games:
        if new_game['name'] not in existing_game_names:
            games_to_add.append(new_game)

    if not games_to_add:
        print("No new games to add")
        return

    # Format new games
    new_games_text = ""
    for game in games_to_add:
        new_games_text += "  {\n"
        new_games_text += f"    name: \"{game['name']}\",\n"
        new_games_text += "    vramByResolution: { "
        new_games_text += f"'1280x720': {game['vramByResolution']['1280x720']}, "
        new_games_text += f"'1920x1080': {game['vramByResolution']['1920x1080']}, "
        new_games_text += f"'2560x1440': {game['vramByResolution']['2560x1440']}, "
        new_games_text += f"'3840x2160': {game['vramByResolution']['3840x2160']} "
        new_games_text += "},\n"
        new_games_text += f"    ram: {game['ram']}\n"
        new_games_text += "  },\n"

    # Insert new games before the closing bracket
    new_content = content[:end_pos] + new_games_text + content[end_pos:]

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Added {len(games_to_add)} new games to {file_path}")
    for game in games_to_add:
        print(f"  - {game['name']}")

def main():
    """
    Main function
    """
    print("Starting to search and add popular 3A and FPS games...\n")

    # Search for games
    new_games = search_popular_games()

    if not new_games:
        print("No new game information found")
        return

    print(f"Found {len(new_games)} potential new games:")
    for game in new_games[:10]:  # Show first 10
        print(f"  - {game['name']} (VRAM: {game['vramByResolution']['1920x1080']}GB @ 1080p, RAM: {game['ram']}GB)")
    if len(new_games) > 10:
        print(f"  ... and {len(new_games) - 10} more")

    print("\n" + "="*50)

    # Add to games file
    add_games_to_games_file(new_games)

    print(f"\nCompleted! Added games to the games list")

if __name__ == "__main__":
    main()
