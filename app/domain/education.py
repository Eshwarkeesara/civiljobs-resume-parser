def normalize_education(education_raw: list[str]) -> set[str]:
    levels = set()

    for line in education_raw:
        l = line.lower()

        if "diploma" in l:
            levels.add("DIPLOMA")

        if "b.tech" in l or "btech" in l:
            levels.add("BTECH")

        if "m.tech" in l or "mtech" in l:
            levels.add("MTECH")

    return levels
