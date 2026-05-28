from pydantic import BaseModel, Field
from typing import Literal

class ModelOutput(BaseModel):
    number_of_hazards: int
    decision: Literal["STOP", "KEEP FORWARD", "TURN LEFT", "TURN RIGHT", "BACK UP"]
    turn_degrees: int = Field(ge=0, le=90)
    recommended_speed: int
    slow_down: bool
