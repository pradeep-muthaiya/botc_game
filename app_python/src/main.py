from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal  # Import from the 'database' folder
import models as models
import random
import string
from fastapi.middleware.cors import CORSMiddleware
from schema import PlayerCreate
from pydantic import BaseModel
import json
import requests
import psutil
import socket
from typing import Optional, List

def generate_game_code():
    """Generates a 6-character game code consisting of uppercase letters and digits."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

app = FastAPI()

# Add CORS middleware to allow frontend requests from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or you can specify the exact frontend origin URL
    allow_credentials=True,
    allow_methods=["*"],  # allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # allows all headers
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class GameCreateRequest(BaseModel):
    player_count: Optional[int | None] = None
    game_version: Optional[str | None] = None
    ai_game_master: Optional[bool | None] = None
    turn: Optional[int | None] = None
    time_of_day: Optional[str | None] = None

class PlayerCreateRequest(BaseModel):
    game_code: str
    player_name: str

def get_ip_address(interface='en0'):
    # Get all network interfaces and their addresses
    interfaces = psutil.net_if_addrs()

    # Check if the specified interface exists
    if interface in interfaces:
        # Get the first address of the interface (IPv4 usually)
        for addr in interfaces[interface]:
            if addr.family == socket.AF_INET:  # Use socket.AF_INET for IPv4
                return addr.address
    return None

@app.get("/get_ip/")
def get_ip():
    interface = 'en0'
    ip = get_ip_address(interface)
    if ip:
        return {"interface": interface, "ip_address": ip}
    else:
        return {"error": f"IP address for interface {interface} not found"}

    
@app.post("/games/")
def create_game(game_data: GameCreateRequest, db: Session = Depends(get_db)):
    errors = []
    game_code = generate_game_code()  # Your function to generate a 6-character game code

    # Ensure unique game_code
    while db.query(models.Game).filter(models.Game.game_code == game_code).first():
        game_code = generate_game_code()

    try:
        db_game = models.Game(
            game_code=game_code,
            player_count=game_data.player_count,
            game_version=game_data.game_version,
            ai_game_master=game_data.ai_game_master,
            turn=game_data.turn,
            time_of_day=game_data.time_of_day
        )
        db.add(db_game)
        db.commit()
        db.refresh(db_game)

        return {"result": "success", "game_code": game_code, "errors": []}

    except Exception as e:
        db.rollback()
        errors.append(str(e))
        return {"result": "failure", "game_code": None, "errors": errors}
    
@app.get("/games/")
def get_all_games(db: Session = Depends(get_db)):
    try:
        games = db.query(models.Game).all()
        return {"result": "success", "games": games}
    except Exception as e:
        return {"result": "failure", "error": str(e)}
    
@app.get("/games/{game_code}")
def get_game_by_code(game_code: str, db: Session = Depends(get_db)):
    try:
        game = db.query(models.Game).filter(models.Game.game_code == game_code).first()
        if game:
            return {"result": "success", "game": game}
        return {"result": "failure", "error": "Game not found"}
    except Exception as e:
        return {"result": "failure", "error": str(e)}

@app.put("/games/{game_id}")
def update_game(game_id: str, game_data: GameCreateRequest, db: Session = Depends(get_db)):
    try:
        print(game_id)
        game = db.query(models.Game).filter(models.Game.game_code == game_id).first()
        if not game:
            return {"result": "failure", "error": "Game not found"}

        if game_data.player_count is not None:
            game.player_count = game_data.player_count
        if game_data.game_version is not None:
            game.game_version = game_data.game_version
        if game_data.ai_game_master is not None:
            game.ai_game_master = game_data.ai_game_master
        if game_data.turn is not None:
            game.turn = game_data.turn
        if game_data.time_of_day is not None:
            game.time_of_day = game_data.time_of_day

        db.commit()
        db.refresh(game)
        return {"result": "success", "game": game}
    except Exception as e:
        db.rollback()
        return {"result": "failure", "error": str(e)}
    

@app.post("/players/")
def create_player(player_data: PlayerCreateRequest, db: Session = Depends(get_db)):
    try:
        db_player = models.Player(
            game_code=player_data.game_code,
            player_name=player_data.player_name,
            character_id=0,
            dead=False,
            vote_token_remaining=True,
            protected=False
        )
        db.add(db_player)
        db.commit()
        db.refresh(db_player)

        return {"result": "success", "player": db_player}
    except Exception as e:
        db.rollback()
        return {"result": "failure", "error": str(e)}

@app.get("/players/game/{game_code}")
def get_players_by_game(game_code: str, db: Session = Depends(get_db)):
    try:
        players = db.query(models.Player).filter(models.Player.game_code == game_code).all()
        return {"result": "success", "players": players}
    except Exception as e:
        return {"result": "failure", "error": str(e)}

@app.get("/players/{player_id}")
def get_player_by_id(player_id: str, db: Session = Depends(get_db)):
    try:

        # Fetch player from database
        player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
        game = db.query(models.Game).filter(models.Game.game_code == player.game_code).first()
        if not player:
            return {"result": "failure", "error": "Player not found"}

        # Prepare player response data
        player_data = {
            "player_id": player.player_id,
            "player_name": player.player_name,
            "game_code": player.game_code,
            "turn": game.turn,
            "character_id": player.character_id,
            "vote_token_remaining": player.vote_token_remaining,
            "creation_date": player.creation_date,
            "dead": player.dead,
            "protected": player.protected
        }

        # Load characters from JSON file
        with open("game_files/trouble_brewing/characters.json", "r") as file:
            characters_data = json.load(file)

        # Find character details if character_id is not 0
        if player.character_id != 0:
            character = next((char for char in characters_data if char["character_id"] == player.character_id), None)
            if character:
                player_data["character"] = {
                    "character_id": character["character_id"],
                    "character_name": character["character_name"],
                    "designation": character["designation"],
                    "character_description": character["character_description"]
                }

        return {"result": "success", "player": player_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Define a model for a single player's update
class PlayerUpdate(BaseModel):
    player_id: str
    character_id: int

# Define a model for the request body
class PlayerUpdateRequest(BaseModel):
    players: list[PlayerUpdate]

@app.put("/players/update_multiple")
def update_multiple_players(request: PlayerUpdateRequest, db: Session = Depends(get_db)):
    try:
        # Now we can access players as request.players
        for player in request.players:
            existing_player = db.query(models.Player).filter(models.Player.player_id == player.player_id).first()
            if not existing_player:
                return {"result": "failure", "error": f"Player {player.player_id} not found"}
            
            if player.character_id is not None:
                existing_player.character_id = player.character_id
            
            db.commit()
            db.refresh(existing_player)

        return {"result": "success", "players": request.players}
    except Exception as e:
        db.rollback()
        return {"result": "failure", "error": str(e)}


@app.put("/players/{player_id}")
def update_player(player_id: str, player_name: str = None, character_id: int = None, dead: bool = None, vote_token_remaining: bool = None, protected: bool = None, db: Session = Depends(get_db)):
    try:
        player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
        if not player:
            return {"result": "failure", "error": "Player not found"}

        if player_name is not None:
            player.player_name = player_name
        if character_id is not None:
            player.character_id = character_id
        if dead is not None:
            player.dead = dead
        if vote_token_remaining is not None:
            player.vote_token_remaining = vote_token_remaining
        if protected is not None:
            player.protected = protected

        db.commit()
        db.refresh(player)
        return {"result": "success", "player": player}
    except Exception as e:
        db.rollback()
        return {"result": "failure", "error": str(e)}
    
@app.post("/characters/")
def create_character(character_name: str, designation: str, game_version: str, character_description: str, power_usage_count: int, power_usage_count_max: int, first_day_order: int = None, night_order: int = None, db: Session = Depends(get_db)):
    try:
        db_character = models.Characters(
            character_name=character_name,
            designation=designation,
            game_version=game_version,
            character_description=character_description,
            power_usage_count=power_usage_count,
            power_usage_count_max=power_usage_count_max,
            first_day_order=first_day_order,
            night_order=night_order
        )
        db.add(db_character)
        db.commit()
        db.refresh(db_character)
        return {"result": "success", "character": db_character}
    except Exception as e:
        db.rollback()
        return {"result": "failure", "error": str(e)}

@app.get("/characters/game_version/{game_version}")
def get_characters_by_game_version(game_version: str, db: Session = Depends(get_db)):
    # try:
    #     characters = db.query(models.Characters).filter(models.Characters.game_version == game_version).all()
    #     return {"result": "success", "characters": characters}
    # except Exception as e:
    #     return {"result": "failure", "error": str(e)}
    try:
        # Read the characters from the JSON file
        with open("game_files/trouble_brewing/characters.json", "r") as file:
            characters_data = json.load(file)
        
        # Filter the characters by the provided game_version
        filtered_characters = [
            character for character in characters_data if character["game_version"] == game_version
        ]

        if not filtered_characters:
            return {"result": "failure", "error": "No characters found for this game version"}

        return {"result": "success", "characters": filtered_characters}
    except Exception as e:
        return {"result": "failure", "error": str(e)}
    
@app.post("/characteractions/")
def create_character_action(character_id: int, time_of_day: str, recieve_information: bool, information_recieved: str, first_day: bool, make_action: bool, action: str, response_required: bool, db: Session = Depends(get_db)):
    try:
        db_action = models.CharacterActions(
            character_id=character_id,
            time_of_day=time_of_day,
            recieve_information=recieve_information,
            information_recieved=information_recieved,
            first_day=first_day,
            make_action=make_action,
            action=action,
            response_required=response_required
        )
        db.add(db_action)
        db.commit()
        db.refresh(db_action)
        return {"result": "success", "character_action": db_action}
    except Exception as e:
        db.rollback()
        return {"result": "failure", "error": str(e)}

@app.get("/character_actions/first_night/{game_version}")
def get_first_night_actions(game_version: str):
    try:
        #print('here', game_version)
        # Load character actions from JSON file
        with open(f"game_files/{game_version}/characteractions.json", "r") as file:
            #print('here2')
            character_actions = json.load(file)
        #print(character_actions)
        # Filter actions where first_night is True
        first_night_actions = [
            action for action in character_actions 
            if action.get("first_night")
        ]
        return {"result": "success", "actions": first_night_actions}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Character actions file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class GameRequest(BaseModel):
    game_code: str
    game_version: str

@app.post("/game/first_night_players")
def get_first_night_players(request: GameRequest, db: Session = Depends(get_db)):
    try:
        
        game_code = request.game_code
        game_version = request.game_version

        game_version_mapping = {
            "Trouble Brewing": "trouble_brewing",
            "trouble_brewing": "trouble_brewing"
        }
        # 1. Get all players in the game
        players = db.query(models.Player).filter(models.Player.game_code == game_code).all()
        if not players:
            raise HTTPException(status_code=404, detail="No players found for this game.")

        # 2. Load all character actions from JSON
        with open(f"game_files/{game_version_mapping[game_version]}/characteractions.json", "r") as file:
            character_actions = json.load(file)
        with open(f"game_files/{game_version_mapping[game_version]}/characters.json", "r") as file:
            characters = json.load(file)

        #print('characteractions: ', character_actions)
        #print('characters: ', characters)
        # 3. Filter only actions for this game version and first-night characters
        first_night_actions = {
            action["character_id"]: action
            for action in character_actions
            if action.get("first_night")
        }


        # 3. Filter only actions for this game version and first-night characters
        first_night_characters = {
            character["character_id"]: character
            for character in characters
            if character.get("first_night_order")
        }

        #print('players: ', players)
        #print('first_night_actions: ', first_night_actions)

        # 4. Find players who have first-night active characters
        first_night_players = []
        for player in players:
            if player.character_id in first_night_actions:
                character_action_info = first_night_actions[player.character_id]
                character_info = first_night_characters[player.character_id]
                first_night_players.append({
                    "player_id": player.player_id,
                    "player_name": player.player_name,
                    "character_id": player.character_id,
                    "dead": player.dead,
                    "vote_token_remaining": player.vote_token_remaining,
                    "protected": player.protected,
                    "character_name": character_info.get("character_name"),
                    "designation": character_info.get("designation"),
                    "first_night_order": character_info.get("first_night_order"),               
                    "character_action_info": character_action_info
                })
            #else:
                

        if not first_night_players:
            return {"result": "failure", "message": "No players have first-night actions."}

        return {"result": "success", "players": first_night_players}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Character actions file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PlayerInfo(BaseModel):
    player_id: str
    character_id: int
    designation: str
    first_night_order: int
    receives_information: bool
    information_received: str
    action: str | None
    response_required: bool

class GameInfoRequest(BaseModel):
    game_code: str
    players: List[PlayerInfo]

@app.post("/game/update_first_night_info")
async def update_first_night_info(game_info: GameInfoRequest, db: Session = Depends(get_db)):
    try:
        # Loop through each player in the request
        for player in game_info.players:
            # Insert a new record into the information table for each player
            new_action = models.Actions(
                player_id=player.player_id,
                action_type="night_info",
                turn=1,  # Assuming it's the first turn, adjust as necessary
                action_input=player.information_received,
                response_required=player.response_required,
                information_id=0
            )
            db.add(new_action)
        
        # Commit the transaction to the database
        db.commit()

        return {"result": "success", "message": "Information saved successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

class InformationSend(BaseModel):
    player_id: str
    information_type: str
    information_input: str
    response_required: bool
    turn: int

@app.post("/player/add_information")
async def add_information(info: InformationSend, db: Session = Depends(get_db)):
    try:
        # Loop through each player in the request
        
        new_info = models.Information(
            player_id=info.player_id,
            turn=info.turn,  # Assuming it's the first turn, adjust as necessary
            information_type=info.information_type,
            information_input=info.information_input,
            response_required=info.response_required,
            action_id = 0
        )
        db.add(new_info)
        
        # Commit the transaction to the database
        db.commit()

        return {"result": "success", "message": "Information saved successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

class ActionSend(BaseModel):
    player_id: str
    action_type: str
    action_input: str
    response_required: bool
    turn: int

@app.post("/player/add_action")
async def add_action(info: ActionSend, db: Session = Depends(get_db)):
    try:
        # Loop through each player in the request
        
        new_info = models.Actions(
            player_id=info.player_id,
            turn=info.turn,  # Assuming it's the first turn, adjust as necessary
            action_type=info.action_type,
            action_input=info.action_input,
            response_required=info.response_required,
            information_id = 0
        )
        db.add(new_info)
        
        # Commit the transaction to the database
        db.commit()

        return {"result": "success", "message": "Information saved successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/actions/delete_all")
def delete_all_actions(db: Session = Depends(get_db)):
    try:
        # Delete all actions
        db.query(models.Actions).delete()
        db.commit()
        return {"result": "success", "message": "All actions deleted successfully"}
    except Exception as e:
        db.rollback()  # Rollback in case of an error
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/player_actions/{game_code}/{player_id}")
def get_player_actions_and_info(game_code: str, player_id: str, db: Session = Depends(get_db)):
    try:
        # Get actions for the player and turn
        game = db.query(models.Game).filter(models.Game.game_code == game_code).all()
        turn = game[0].turn
        actions = db.query(models.Actions).filter(models.Actions.player_id == player_id, models.Actions.turn == turn).all()
        information = db.query(models.Information).filter(models.Information.player_id == player_id, models.Information.turn == turn).all()

        result = []

        for action in actions:

            # Add the action along with its corresponding information if available
            action_info = {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "action_input": action.action_input,
                "turn": action.turn,
                "response_required": action.response_required,
            }

            result.append(action_info)

        information_result = []
        for info in information:
            information_info = {
                "information_id": info.information_id,
                "information_type": info.information_type,
                "information_input": info.information_input,
                "turn": info.turn,
                "response_required": info.response_required,
            }
            information_result.append(information_info)

        return {
            "result": "success",
            "actions": result,
            "information": information_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/all_players_info/{game_code}")
def get_player_actions_and_info(game_code: str, db: Session = Depends(get_db)):
    try:
        # Get actions for the player and turn
        game = db.query(models.Game).filter(models.Game.game_code == game_code).all()
        turn = game[0].turn
        actions = db.query(models.Actions).filter(models.Actions.turn == turn).all()
        information = db.query(models.Information).filter(models.Information.turn == turn).all()

        result = {}

        for action in actions:

            # Add the action along with its corresponding information if available
            action_info = {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "action_input": action.action_input,
                "turn": action.turn,
                "response_required": action.response_required,
            }

            if action.player_id not in result:
                result[action.player_id] = [action_info]
            else:
                result[action.player_id].append(action_info)

        information_result = {}
        for info in information:
            information_info = {
                "player_id": info.player_id,
                "information_id": info.information_id,
                "information_type": info.information_type,
                "information_input": info.information_input,
                "turn": info.turn,
                "response_required": info.response_required,
            }
            if action.player_id not in information_result:
                information_result[action.player_id] = [information_info]
            else:
                information_result[action.player_id].append(information_info)

        return {
            "result": "success",
            "actions": result,
            "information": information_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))