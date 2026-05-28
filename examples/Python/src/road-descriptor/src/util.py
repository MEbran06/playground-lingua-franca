from pydantic import BaseModel
from typing import Literal

class ModelOutput(BaseModel):
    number_of_hazards: int
    decision: Literal["STOP", "KEEP FORWARD", "TURN LEFT", "TURN RIGHT", "BACK UP"]
    recommended_speed: int
    slow_down: bool
