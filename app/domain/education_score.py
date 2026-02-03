def score_education(levels: set[str]) -> int:
    """
    Scores education based on qualification combinations.
    Authoritative scoring as per Civil Jobs framework.
    """

    if levels == {"DIPLOMA"}:
        return 50

    if levels == {"BTECH"}:
        return 70

    if levels == {"DIPLOMA", "BTECH"}:
        return 80

    if levels == {"BTECH", "MTECH"}:
        return 85

    if levels == {"DIPLOMA", "BTECH", "MTECH"}:
        return 100

    # Defensive fallback (in case of noisy resumes)
    if "MTECH" in levels:
        return 85
    if "BTECH" in levels:
        return 70
    if "DIPLOMA" in levels:
        return 50

    return 0
