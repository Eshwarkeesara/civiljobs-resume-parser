SKILLS = [
    "project management",
    "planning",
    "billing",
    "civil engineering",
    "construction",
    "qa/qc",
    "contracts",
    "tendering"
]

def extract_skills(text: str) -> list[str]:
    t = text.lower()
    return [skill for skill in SKILLS if skill in t]
