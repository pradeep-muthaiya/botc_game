from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base  # Update the import to use database_src
from datetime import datetime
from random import randint

class Game(Base):
    __tablename__ = "games"  # Table name in the database

    # Define the columns
    id = Column(Integer, primary_key=True, index=True)  # Unique ID for each row
    game_code = Column(String(6), unique=True, index=True, nullable=False)  # 6-character game code
    player_count = Column(Integer, nullable=False)  # Player count as an integer
    created_date = Column(DateTime, default=func.now(), nullable=False)  # Creation time (default is the current time)
    game_version = Column(String(50), nullable=False) # Version of the game
    ai_game_master = Column(Boolean, nullable=False)
    turn = Column(Integer, nullable=False)
    time_of_day = Column(String(10), nullable=False) #Can be Day, Voting, Night
    
class Player(Base):
    __tablename__ = "players"

    player_id = Column(String(10), primary_key=True, default=lambda: str(randint(10**9, 10**10 - 1)))
    game_code = Column(String(6), ForeignKey("games.game_code"), nullable=False)
    player_name = Column(String(50), nullable=False)
    creation_date = Column(DateTime, default=func.now(), nullable=False)
    character_id = Column(Integer, nullable=False)
    dead = Column(Boolean, nullable=False)
    vote_token_remaining = Column(Boolean, nullable=False)
    protected = Column(Boolean, nullable=True)

class Actions(Base):
    __tablename__ = "actions"

    action_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(10), nullable=False)
    action_type = Column(String(50), nullable=False) # Either elect, vote or night_response,
    action_input = Column(String(255), nullable=False)
    turn = Column(Integer, nullable=False)
    response_required = Column(Boolean, nullable=False)
    information_id = Column(Integer, nullable=False) #info id it is actioning based on

class Information(Base):
    __tablename__ = "information"

    information_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(String(10), nullable=False)
    turn = Column(Integer, nullable=False)
    information_type = Column(String(10), nullable=False) 
    information_input = Column(String(255), nullable=False)
    response_required = Column(Boolean, nullable=False)
    action_id = Column(Integer, nullable=False) #action_id that the information is responding_to

class Characters(Base):
    __tablename__ = "characters"

    character_id = Column(Integer, primary_key=True, index=True)
    character_name = Column(String(50), nullable=False)
    designation = Column(String(10), nullable=False) #either demon, imp, villager, outsider
    game_version = Column(String(50), nullable=False)
    character_description = Column(String(255), nullable=False)
    power_usage_count = Column(Integer, nullable=False)
    power_usage_count_max = Column(Integer, nullable=False)
    first_day_order = Column(Integer)
    night_order = Column(Integer, nullable=False)

class CharacterActions(Base):
    __tablename__ = "characteractions"

    character_action_id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, nullable=False)
    time_of_day = Column(String(10), nullable=False)
    recieve_information = Column(Boolean, nullable=False)
    information_recieved = Column(String(255), nullable=False)
    first_night = Column(Boolean, nullable=False)
    make_action = Column(Boolean, nullable=False)
    action = Column(String(255), nullable=False)
    response_required = Column(Boolean, nullable=False)

    


    




