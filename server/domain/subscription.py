from dataclasses import dataclass

@dataclass(frozen=True)
class Subscription:
    user_id: str
