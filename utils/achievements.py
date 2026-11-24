import json

ACHIEVEMENTS_MAP = {
    "first_grow": "🌱 Первый рост",
    "size_100": "💪 100 см",
    "size_250": "🚀 250 см",
    "size_500": "👑 500 см",
    "size_1000": "🔥 1000 см"
}

def check_achievements(current_achievements_json: str, new_size: int, attempts: int) -> tuple[str, list[str]]:
    achievements = json.loads(current_achievements_json)
    new_achievements = []

    if attempts >= 1 and "first_grow" not in achievements:
        achievements.append("first_grow")
        new_achievements.append(ACHIEVEMENTS_MAP["first_grow"])
    if new_size >= 100 and "size_100" not in achievements:
        achievements.append("size_100")
        new_achievements.append(ACHIEVEMENTS_MAP["size_100"])
    if new_size >= 250 and "size_250" not in achievements:
        achievements.append("size_250")
        new_achievements.append(ACHIEVEMENTS_MAP["size_250"])
    if new_size >= 500 and "size_500" not in achievements:
        achievements.append("size_500")
        new_achievements.append(ACHIEVEMENTS_MAP["size_500"])
    if new_size >= 1000 and "size_1000" not in achievements:
        achievements.append("size_1000")
        new_achievements.append(ACHIEVEMENTS_MAP["size_1000"])

    return json.dumps(achievements), new_achievements