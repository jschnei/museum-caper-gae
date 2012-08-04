# models
from google.appengine.ext import db
import pickle

from game_util import Character
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

    # add a piece for this new user
    character = Character(pos_x = pos_x, 
                          pos_y = pos_y, 
                          img_file = 'piece.png', 
                          uid = uid)

    self.add_character(character)

  def add_user_id(self, uid):
    self.user_ids.append(uid)

  def load_map(self):
    return map_util.load_map(self.map_file, self.load_pieces())

  def load_piece(piece_ind):
    return pickle.loads(str(self.character_list[piece_ind]))

  def load_pieces(self):
    return [pickle.loads(str(pickled)) for pickled in self.character_list]

  def load_users(self):
    return [User.get_by_id(uid) for uid in self.user_ids]

  def load_cur_piece(self, return_ind=False):
    game_pieces = self.load_pieces()
    game_users = self.load_users()

    cur_turn = self.turn_num % len(game_pieces)

    if return_ind:
      return game_pieces[cur_turn], cur_turn
    else:
      return game_pieces[cur_turn]

  def load_cur_user(self):
    cur_piece = self.load_cur_piece()
    cur_uid = cur_piece.uid

    cur_user = None
    for game_user in self.load_users():
      if game_user.key().id() == cur_uid:
        cur_user = game_user

    return cur_user

  def update_piece(self, piece, piece_ind):
    self.character_list[piece_ind] = pickle.dumps(piece)
  
  # Tries to move piece in direction pos_diff (if piece=None, then uses 
  # the current piece). Returns True if successful.
  def make_move(self, pos_diff, piece_ind=None):
    if piece_ind:
      piece = self.load_piece(piece_ind)
    else:
      piece, piece_ind = self.load_cur_piece(return_ind=True)
    
    game_map = self.load_map()

    if not game_map.valid_move(piece, pos_diff):
      return False
    else:
      # perform move 
      piece.move(pos_diff[0], pos_diff[1])
      self.update_piece(piece, piece_ind)

      # increase the turn number by 1
      self.turn_num += 1

      return True

  def num_players(self):
    return len(self.user_ids)
