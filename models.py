# models
from google.appengine.ext import db

class User(db.Model):
  name = db.StringProperty(required = True)
  password = db.StringProperty(required = True)
  email = db.StringProperty(required = True)

  game_ids = db.ListProperty(int)

  created = db.DateTimeProperty(auto_now_add = True)

class Game(db.Model):
  user_ids = db.ListProperty(int)
  
  game_state = db.StringProperty(default = 'pregame')

  turn_num = db.IntegerProperty(required = True, default = 0)
  map_file = db.StringProperty(default = 'default_map.map')
  piece_list = db.ListProperty(str)

  created = db.DateTimeProperty(auto_now_add = True)

  def num_players(self):
    return len(self.user_ids)