from pydantic import BaseModel, field_validator


class Position(BaseModel):
    latitude: float
    longitude: float

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def to_float(cls, v):
        return float(v)


class ISSResponse(BaseModel):
    timestamp: int
    iss_position: Position


class Astronaut(BaseModel):
    name: str
    craft: str


class AstrosResponse(BaseModel):
    number: int
    people: list[Astronaut]
