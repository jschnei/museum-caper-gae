#!/usr/bin/env python

from google.appengine.ext import db

import jinja2
import os
import pickle
import webapp2

from models import *
from game_util import Piece, Character, Painting, Lock

import auth_util
import map_util
import game_util

jinja_loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
jinja_env = jinja2.Environment(autoescape=True,
	                             loader = jinja_loader)

# handlers

class MainHandler(webapp2.RequestHandler):
  def render(self):
    template = jinja_env.get_template('main.html')
    self.response.out.write(template.render())

  def get(self):
    if auth_util.auth_into_site(self) :
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
    if auth_util.auth_into_site(self) :
      # redirect to games
      self.redirect('/games')
    else:
      self.render()

  def post(self):
    if auth_util.auth_into_site(self) :
      # redirect to games
      self.redirect('/games')
    else:
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
    if auth_util.auth_into_site(self):
      self.redirect('/games')
    else:
      self.render()

  def post(self):
    if auth_util.auth_into_site(self):
      self.redirect('/games')
    else:      
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
    uid = auth_util.auth_into_site(self)
    if uid:
      user = User.get_by_id(uid)
      games = user.game_ids
      self.render(games)
    else:
      self.redirect('/login')

class CreateGameHandler(webapp2.RequestHandler):
  def get(self):
    uid = auth_util.auth_into_site(self)
    if uid:
      user = User.get_by_id(uid)

      # create a new game
      game = Game(user_ids = [uid], 
                  turn_num = 0, 
                  game_state = 'pregame',
                  map_file = 'default_map.map', 
                  character_list = [])
      game.put()
      gid = game.key().id()

      # add gid to user's list of games
      user.game_ids.append(gid)
      user.put()

      self.redirect('/games/game%i' % gid)
    else:
      self.redirect('/login')


class GameHandler(webapp2.RequestHandler):
  def render(self, game, gid, game_data, user, error):
    template = jinja_env.get_template('game.html')
    html = template.render(game = game, 
                           gid = gid, 
                           game_data = game_data,
                           user = user,
                           error = error)
    self.response.out.write(html)


  def get(self, gid):
    uid, gid, user, game = auth_util.auth_into_game(self, gid, 
                                                          ['pregame',
                                                           'init', 
                                                           'inplay'])
    
    
    game_map = game.load_map()
    game_users = game.load_users()
    game_pieces = game.load_pieces()
    cell_images = game_map.get_cell_images()
    cur_user = game.load_cur_user()
    has_placed = game.has_placed(uid)
    # lump into dict

    game_data = {'game_map' : game_map,
                 'game_users': game_users,
                 'game_pieces': game_pieces,
                 'cell_images': cell_images,
                 'cur_user' : cur_user,
                 'has_placed': has_placed}

    # finally check if there were any errors

    if self.request.get('error') == 'y':
      error = True
    else:
      error = False

    # render page

    self.render(game, gid, game_data, user, error)


class MoveHandler(webapp2.RequestHandler):
  def get(self, gid):
    uid, gid, user, game = auth_util.auth_into_game(self, gid, ['inplay'])
    
    # get the direction
    direction = self.request.get('d')

    vectors = {'left': (-1, 0), 'up': (0, -1), 'right': (1, 0), 'down': (0, 1)}
    pos_diff = vectors[direction]

    # make move
    if not game.make_move(pos_diff):
      self.redirect('../game%i?error=y'%gid)
    else:
      game.put()
      self.redirect('../game%i' % gid)


class AddPlayerHandler(webapp2.RequestHandler):
  def post(self, gid):
    uid, gid, user, game = auth_util.auth_into_game(self, gid, ['pregame'])
    
    username = self.request.get('username')
    query = db.Query(User)
    query.filter('name =', username)
    new_user = query.get()

    if new_user:
      # add user and update the game
      game.add_new_user(new_user.key().id())
      game.put()

      # now update the user
      new_user.add_game_id(gid)
      new_user.put()

      # redirect back to the main page
      self.redirect('../game%i' % gid)
    else:
      # this user doesn't exist
      # TODO: send an error message back
      self.redirect('../game%i?error=y' % gid)

class PlacePlayerHandler(webapp2.RequestHandler):
  def get(self, gid):
    uid, gid, user, game = auth_util.auth_into_game(self, gid, ['init'])

    if not game.load_piece_by_uid(uid):
      place_x = int(self.request.get('x'))
      place_y = int(self.request.get('y'))
      place_pos = (place_x, place_y)
      if game.load_map().valid_placement((place_x, place_y)):
        new_character = Character(place_x,
                                  place_y,
                                  game.random_color(),
                                  uid)
        game.add_character(new_character)
        
        if game.ready_to_play():
          game.game_state = 'inplay'
        
        game.put()
        self.redirect('../game%i' % gid)

    self.redirect('../game%i?error=y' % gid)



class StartGameHandler(webapp2.RequestHandler):
  def post(self, gid):
    uid, gid, user, game = auth_util.auth_into_game(self, gid, ['pregame'])
    
    game.game_state = 'init'
    game.put()

    self.redirect('/games/game%i' % gid)

app = webapp2.WSGIApplication([('/', MainHandler), 
                               ('(.*)/', TrailingHandler),
                               ('/login', LoginHandler),
                               ('/register', RegisterHandler),
                               ('/logout', LogoutHandler),
                               ('/games', ViewGamesHandler),
                               ('/creategame', CreateGameHandler),
                               ('/games/game(\d+)', GameHandler),
                               ('/games/game(\d+)/addplayer', AddPlayerHandler),
                               ('/games/game(\d+)/move', MoveHandler),
                               ('/games/game(\d+)/placeplayer', PlacePlayerHandler),
                               ('/games/game(\d+)/startgame', StartGameHandler)
                               ],
                              debug=True)
