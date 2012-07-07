#!/usr/bin/env python

from google.appengine.ext import db

import jinja2
import os
import pickle
import webapp2

from game_util import Piece, CharacterPiece, PaintingPiece, LockPiece

import auth_util
import map_util
import game_util

jinja_loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
jinja_env = jinja2.Environment(autoescape=True,
	                             loader = jinja_loader)


# models

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
        query = db.Query(User)
        query.filter('name =', username)
        query.filter('password =', password)
        rdusers = list(query.run())
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

    
    # check if username is already taken
    query = db.Query(User)
    query.filter('name =', username)
    if query.get():
      errors.append("That user name is already taken")


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

class CreateGameHandler(webapp2.RequestHandler):
  def get(self):
    auth = self.request.cookies.get('auth', '')
    if auth_util.check_cookie(auth) :
      # get user id + user
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)

      # create a new game
      user_piece = CharacterPiece(pos_x = 6, 
                                  pos_y = 5, 
                                  img_file = 'piece.png', 
                                  uid = uid)
      game = Game(user_ids = [uid], 
                  turn_num = 0, 
                  game_state = 'pregame',
                  map_file = 'default_map.map', 
                  piece_list = [pickle.dumps(user_piece)])
      game.put()
      gid = game.key().id()

      # add gid to user's list of games
      user.game_ids.append(gid)
      user.put()

      self.redirect('/games/game%i' % gid)
    else:
      self.redirect('/login')

class GameHandler(webapp2.RequestHandler):
  def render(self, game, gid, game_data, error):
    template = jinja_env.get_template('game.html')
    html = template.render(game = game, 
                           gid = gid, 
                           game_data = game_data,
                           error = error)
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

        # get game users (so we can do things like display their usernames)
        game_users = [User.get_by_id(uid) for uid in game.user_ids]

        # lump into dict

        game_data = {'game_map' : game_map,
                     'game_users': game_users,
                     'game_pieces': game_pieces,
                     'cell_images': cell_images}

        # finally check if there were any errors

        if self.request.get('error') == 'y':
          error = True
        else:
          error = False

        # render page

        self.render(game, gid, game_data, error)
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
      # and whether the game has actually started
      if not game or uid not in game.user_ids:
        self.redirect('/games')
      elif game.game_state != 'inplay':
        # we don't want to let people move before the game starts
        # or after it's over!
        self.redirect('/games/game%i' % gid)
      else:
        # get the direction
        direction = self.request.get('d')

        vectors = {'left': (-1, 0), 'up': (0, -1), 'right': (1, 0), 'down': (0, 1)}
        pos_diff = vectors[direction]


        # get the current piece

        cur_turn = game.turn_num % len(game.piece_list)
        cur_piece = pickle.loads(str(game.piece_list[cur_turn]))

        # get the map
        
        game_map = map_util.load_from_file(game.map_file)

        # check if move is valid

        if not game_map.valid_move(cur_piece.position, pos_diff):
          self.redirect('../game%i?error=y'%gid)
        else:
          # perform move 

          cur_piece.move(pos_diff[0], pos_diff[1])
          game.piece_list[cur_turn] = pickle.dumps(cur_piece)

          # increase the turn number by 1
          game.turn_num += 1

          game.put()
          self.redirect('../game%i' % gid)
    else:
      self.redirect('/login')

class AddPlayerHandler(webapp2.RequestHandler):
  def post(self, gid):
    auth = self.request.cookies.get('auth', '')
    gid = int(gid)

    if auth_util.check_cookie(auth):
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)
      game = Game.get_by_id(gid)

      # check if user actually belongs to this game
      # and whether the game has actually started
      if not game or uid not in game.user_ids:
        self.redirect('/games')
      elif game.game_state != 'pregame':
        # we don't want to let people add people if it's not
        # pregame!
        self.redirect('/games/game%i' % gid)
      else:
        username = self.request.get('username')
        query = db.Query(User)
        query.filter('name =', username)
        new_user = query.get()
        if new_user:
          new_uid = new_user.key().id()
          game.user_ids.append(new_uid)

          # add a piece for this new user
          new_piece = CharacterPiece(pos_x = 6, 
                                      pos_y = 5, 
                                      img_file = 'piece.png', 
                                      uid = uid)
          game.piece_list.append(pickle.dumps(new_piece))

          # update the game
          game.put()

          # now update the user
          new_user.game_ids.append(gid)
          new_user.put()

          # redirect back to the main page
          self.redirect('../game%i' % gid)
        else:
          # this user doesn't exist
          # TODO: send an error message back
          self.redirect('../game%i?error=y' % gid)
    else:
      self.redirect('/login')

class StartGameHandler(webapp2.RequestHandler):
  def post(self, gid):
    auth = self.request.cookies.get('auth', '')
    gid = int(gid)

    if auth_util.check_cookie(auth):
      uid = auth_util.get_uid(auth)
      user = User.get_by_id(uid)
      game = Game.get_by_id(gid)

      # check if user actually belongs to this game
      # and whether the game has actually started
      if not game or uid not in game.user_ids:
        self.redirect('/games')
      elif game.game_state != 'pregame':
        # it doesn't make sense to start the game
        # if we are not in pregame
        self.redirect('/games/game%i' % gid)
      else:
        game.game_state = 'inplay'
        game.put()
        
        self.redirect('/games/game%i' % gid)
    else:
      self.redirect('/login')

app = webapp2.WSGIApplication([('/', MainHandler), 
                               ('(.*)/', TrailingHandler),
                               ('/login', LoginHandler),
                               ('/register', RegisterHandler),
                               ('/logout', LogoutHandler),
                               ('/games', ViewGamesHandler),
                               ('/creategame', CreateGameHandler),
                               ('/games/game(\d+)', GameHandler),
                               ('/games/game(\d+)/move', MoveHandler),
                               ('/games/game(\d+)/addplayer', AddPlayerHandler),
                               ('/games/game(\d+)/startgame', StartGameHandler)
                               ],
                              debug=True)