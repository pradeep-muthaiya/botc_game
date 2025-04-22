from pydantic import BaseModel
from typing import Optional

class PlayerCreate(BaseModel):
    game_code: str
    player_name: str
    icon_image: Optional[str] = None  # i