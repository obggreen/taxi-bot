from beanie import Document


class Link(Document):
    name: str
    short_link: str

    class Settings:
        validate_on_save = True
