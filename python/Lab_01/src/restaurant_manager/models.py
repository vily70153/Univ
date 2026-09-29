from dataclasses import dataclass, field

@dataclass
class dish:
    name: str
    category: str
    price: float

@dataclass
class order:
    number: int
    dishes: list[dish] = field(default_factory=list)