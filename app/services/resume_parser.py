class ResumeParserService:
    def parse(self, file_path):
        return {
            "name": None,
            "email": None,
            "phone": None,
            "education": [],
            "experience": [],
            "skills": []
        }
