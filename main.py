#!/usr/bin/env python

from google.appengine.ext import db

import jinja2
import os
import pickle
import webapp2

import auth_util
import map_util

jinja_loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
jinja_env = jinja2.Environment(autoescape=True,
	                             loader = jinja_loader)

## Piece classes

# 'abstract' Piece class
class Piece(object):
  def __init__(self, pos_x, pos_y, img_file):
    self.position = (pos_x, pos_y)
    self.img_file = img_file

  def move(self, dx, dy):
    self.position = (self.position[0] + dx, self.position[1] + dy)

  def move_abs(self, x, y):
    self.position = (x, y)


class CharacterPiece(Piece):
  def __init__(self, pos_x, pos_y, img_file, uid):
    super(CharacterPiece, self).__init__(pos_x, pos_y, img_file)
    self.uid = uid


class PaintingPiece(Piece):
  def __init__(self):
    # insert later
    return

class LockPiece(Piece):
  def __init__(self):
    # insert later
    return


# models

class User(db.Model):
  name = db.StringProperty(required = True)
  password = db.StringProperty(required = True)
  email = db.StringProperty(required = True)

  game_ids = db.ListProperty(int)

  created = db.DateTimeProperty(auto_now_add = True)

class Game(db.Model):
  user_ids = db.ListProperty(int)
  
  turn_num = db.IntegerProperty(required = True, default = 0)
  map_file = db.StringProperty(default = 'basic_map.map')
  piece_list = db.ListProperty(str)

  created = db.DateTimeProperty(auto_now_add = True)

  def num_players(self):
    return len(self.user_ids)


# handlers

class MainHandler(webapp2.RequestHandler):
  def render(self):
    template = jinja_env.get_template('main.html')
    self.response.out.write(template.render())

  def get(self):
    auth = self.request.cookies.get('auth', '')
    if auth_util.check_cookie(auth) :
      # redirect to games
      self.redirect('/games')
    else:
      self.render()

# deal with trailing /s
class TrailingHandler(webapp2.RequestHandler):
  def get(self, path):
    self.redirect(path)

class LoginHandler(webapp2.RequestHandler):
  def render(self, errors = None):
    template = jinja_env.get_template('login.html')
    html = template.render(errors = errors)
    self.response.out.write(html)

  def get(self):
    self.render()

  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')

    errors = []

    vUser = auth_util.valid_username(username)
    vPass = auth_util.valid_password(password)


    if vUser and vPass:
        users = db.GqlQuery("SELECT * FROM User")
        rdusers = ([u for u in users if u.name == username and u.password == password])
        if rdusers:
            u = rdusers[0]
            uid = u.key().id()
            auth = auth_util.gen_cookie(uid)
            self.response.headers.add_header('Set-Cookie', 'auth = %s; Path = /' % auth)
            self.redirect('/')
        else:
            errors.append('Invalid Username/Password Combination')
    else:
        errors.append('Invalid Username/Password Combination')

    self.render(errors)


class RegisterHandler(webapp2.RequestHandler):
  def render(self, errors = None):
    template = jinja_env.get_template('register.html')
    html = template.render(errors = errors)
    self.response.out.write(html)

  def get(self):
    self.render()

  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    verify = self.request.get('verify')
    email = self.request.get('email')

    errors = []
    if not auth_util.valid_username(username):
      errors.append("That's not a valid username")
    if not auth_util.valid_password(password):
      errors.append("That's not a valid password")
    if not auth_util.valid_verify(verify, password):
      errors.append("Your passwords do not match")
    if not auth_util.valid_email(email):
      errors.append("That's not a valid e-mail")

    if not errors:
      u = User(name = username, password = password, email = email)
      u.put()
      uid = u.key().id()
      auth = auth_util.gen_cookie(uid)
      self.response.headers.add_header('Set-Cookie', 'auth = %s; Path = /' % auth)
      self.redirect('/')
    else:
      self.render(errors)

class LogoutHandler(webapp2.RequestHandler):
  def get(self):
    self.response.headers.add_header('Set-Cookie', 'auth=; Path=/')
    self.redirect('/')

class ViewGamesHandler(webapp2.RequestHandler):
  def render(self, games = None):
    template = jinja_env.get_template('viewgames.html')
    html = template.render(games = games)
    self.response.out.write(html)

  def get(self):
    auth = self.request.cookies.get('auth', '')
    if auth_util.check_cookie(auth):
      # get users games
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)
      games = user.game_ids
      self.render(games)
    else:
      self.redirect('/login')

class StartGameHandler(webapp2.RequestHandler):
  def get(self):
    auth = self.request.cookies.get('auth', '')
    if auth_util.check_cookie(auth) :
      # get user id + user
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)

      # create a new game
      user_piece = CharacterPiece(pos_x = 10, pos_y = 10, img_file = 'piece.png', uid = uid)
      game = Game(user_ids = [uid], 
                  turn_num = 0, 
                  map_file = 'basic_map.map', 
                  piece_list = [pickle.dumps(user_piece)])
      game.put()
      gid = game.key().id()

      # add gid to user's list of games
      user.game_ids.append(gid)
      user.put()

      self.redirect('/games')
    else:
      self.redirect('/login')

class GameHandler(webapp2.RequestHandler):
  def render(self, game, gid, game_data):
    template = jinja_env.get_template('game.html')
    html = template.render(game = game, 
                           gid = gid, 
                           game_data = game_data)
    self.response.out.write(html)

  def get(self, gid):
    auth = self.request.cookies.get('auth', '')
    try:
      gid = int(gid)
    except (ValueError, TypeError):
      self.redirect('/games')
    if auth_util.check_cookie(auth):
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)
      game = Game.get_by_id(gid)

      # check if user actually belongs to this game
      if not game or uid not in game.user_ids:
        self.redirect('/games')
      else:
        # get game map
        game_map = map_util.load_from_file(game.map_file)

        # get game pieces
        game_pieces = [pickle.loads(str(pickled)) for pickled in game.piece_list]

        # get image files for each cell

        # first non-piece images
        cell_images = { }
        for pos, val in game_map.data.items():
          cell_images[pos] = 'cell%i.png' % val

        # next piece images
        for piece in game_pieces:
          cell_images[piece.position] = piece.img_file

        # lump into dict

        game_data = {'game_map' : game_map,
                    'game_pieces': game_pieces,
                    'cell_images': cell_images}
        self.render(game, gid, game_data)
    else:
      self.redirect('/login')

class MoveHandler(webapp2.RequestHandler):
  def get(self, gid):
    auth = self.request.cookies.get('auth', '')
    gid = int(gid)

    if auth_util.check_cookie(auth):
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)
      game = Game.get_by_id(gid)

      # check if user actually belongs to this game
      if not game or uid not in game.user_ids:
        self.redirect('/games')
      else:
        # get the direction
        direction = self.request.get('d')

        vectors = {'left': (-1, 0), 'up': (0, -1), 'right': (1, 0), 'down': (0, 1)}
        pos_diff = vectors[direction]


        # get the current piece and move it

        cur_turn = game.turn_num % len(game.piece_list)
        cur_piece = pickle.loads(str(game.piece_list[cur_turn]))

        # get the map
        
        game_map = map_util.load_from_file(game.map_file)

        # check if move is valid

        if not game_map.valid_move(cur_piece.position, pos_diff):
          self.redirect('../game%i?e=1'%gid)
        else:
          # perform move 

          cur_piece.move(pos_diff[0], pos_diff[1])
          game.piece_list[cur_turn] = pickle.dumps(cur_piece)

          # increase the turn number by 1
          game.turn_num += 1

          game.put()
          self.redirect('../game%i'%gid)
    else:
      self.redirect('/login')

app = webapp2.WSGIApplication([('/', MainHandler), 
                               ('(.*)/', TrailingHandler),
                               ('/login', LoginHandler),
                               ('/register', RegisterHandler),
                               ('/logout', LogoutHandler),
                               ('/games', ViewGamesHandler),
                               ('/startgame', StartGameHandler),
                               ('/games/game(\d+)', GameHandler),
                               ('/games/game(\d+)/move', MoveHandler),
                               ],
                              debug=True)