# models
from google.appengine.ext import db

import pickle
import random

from game_util import Character

import game_util
import map_util


class User(db.Model):
  name = db.StringProperty(required = True)
  password = db.StringProperty(required = True)
  email = db.StringProperty(required = True)

  game_ids = db.ListProperty(int)

  created = db.DateTimeProperty(auto_now_add = True)

  
  def add_game_id(self, gid):
    self.game_ids.append(gid)


class Game(db.Model):
  user_ids = db.ListProperty(int)
  
  game_state = db.StringProperty(default = 'pregame')

  turn_num = db.IntegerProperty(required = True, default = 0)
  map_file = db.StringProperty(default = 'default_map.map')
  character_list = db.ListProperty(str)

  created = db.DateTimeProperty(auto_now_add = True)


  def add_character(self, piece):
    self.character_list.append(pickle.dumps(piece))


  def add_new_user(self, uid, pos_x = 5, pos_y = 6):
    self.add_user_id(uid)


  def add_user_id(self, uid):
    self.user_ids.append(uid)


  def get_piece_ind(self, piece):
    game_pieces = self.load_pieces()
    for ind in xrange(len(game_pieces)):
      if game_pieces[ind].uid == piece.uid:
        return ind


  def has_placed(self, uid):
    if not self.load_piece_by_uid(uid):
      return False
    else:
      return True


  def load_map(self):
    return map_util.load_map(self.map_file, self.load_pieces())


  def load_piece(piece_ind):
    return pickle.loads(str(self.character_list[piece_ind]))


  def load_piece_by_uid(self, uid):
    for piece in self.load_pieces():
      if piece.uid == uid:
        return piece
  

  def load_piece_by_user(self, user):
    return self.load_piece_by_uid(user.key().id())


  def load_pieces(self):
    return [pickle.loads(str(pickled)) for pickled in self.character_list]


  def load_users(self):
    return [User.get_by_id(uid) for uid in self.user_ids]


  def load_cur_piece(self):
    return self.load_piece_by_uid(self.load_cur_uid())

  def load_cur_turn(self):
    return self.turn_num % len(self.user_ids)


  def load_cur_uid(self):
    return self.user_ids[self.load_cur_turn()]
    

  def load_cur_user(self):
    return User.get_by_id(self.load_cur_uid())


  def update_piece(self, piece, piece_ind=None):
    if not piece_ind:
        piece_ind = self.get_piece_ind(piece)
    self.character_list[piece_ind] = pickle.dumps(piece)
    
  
  # Tries to move piece in direction pos_diff (if piece=None, then uses 
  # the current piece). Returns True if successful.
  def make_move(self, pos_diff, piece_ind=None):
    if piece_ind:
      piece = self.load_piece(piece_ind)
    else:
      piece = self.load_cur_piece()
    
    game_map = self.load_map()

    if not game_map.valid_move(piece, pos_diff):
      return False
    else:
      # perform move 
      piece.move(pos_diff[0], pos_diff[1])
      self.update_piece(piece)

      # increase the turn number by 1
      self.turn_num += 1

      return True


  def random_color(self):
    # TODO: Allow players to select their colors!
    used_colors = {char.color for char in self.load_pieces()}
    return random.sample(game_util.VALID_COLORS - used_colors, 1)[0]
  

  def ready_to_play(self):
    return (len(self.user_ids) == len(self.character_list))

  
  def num_players(self):
    return len(self.user_ids)
