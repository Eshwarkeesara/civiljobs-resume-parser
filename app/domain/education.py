def detect_education_levels(text: str) -> set[str]:
    t = text.lower()
    levels = set()

    if "diploma" in t:
        levels.add("DIPLOMA")
    if "b.tech" in t or "bachelor of technology" in t:
        levels.add("BTECH")
    if "m.tech" in t or "master of technology" in t:
        levels.add("MTECH")

    return levels
