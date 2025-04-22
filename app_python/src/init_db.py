from database import engine, Base
from models import Game, Player

print('running...')
# Create the database tables
Base.metadata.create_all(bind=engine)
