from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    username: str
    email: str
    password: str
