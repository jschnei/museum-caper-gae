# authutil.py
# This is a module that contains useful functions for authorization (login/signup)
# that are independent of the main webpage flow.

import hashlib
import re
import webapp2

from models import *

# cookie hash secret
SECRET = 'linenoise'

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^^[\S]+@[\S]+\.[\S]+$$")

# top-level handler authentication


# handles all of the work for authenticating into a game
# (checking that the user is logged in, the user belongs in
# that game, the game is in the right state, redirecting the
# user if any of this isn't true, etc.)
def auth_into_game(handler, gid, game_states):
    auth = handler.request.cookies.get('auth', '')
    gid = int(gid)

    if check_cookie(auth):
      uid = get_uid(auth)
      user = User.get_by_id(uid)
      game = Game.get_by_id(gid)

      # check if user actually belongs to this game
      # and whether the game has actually started
      if not game or uid not in game.user_ids:
        handler.redirect('/games')
      elif game.game_state not in game_states:
        # we don't want to let people add people if we're not in the 
        # desired game_state
        handler.redirect('/games/game%i' % gid)
      
      return uid, gid, user, game
    else:
      self.redirect('/login')

# checks whether the user has a valid cookie
# and is allowed to auth into the site
# if the user is, it returns the UID
# otherwise it returns None 
# (as opposed to auth_into_game doesn't
# do any redirects since for some pages
# we want the user to be logged in and for
# others we don't)
def auth_into_site(handler):
  auth = handler.request.cookies.get('auth', '')
  if check_cookie(auth):
    uid = get_uid(auth)  

    if not User.get_by_id(uid):
      # their cookie is valid, but this user doesn't
      # actually exist (it was maybe deleted, or the user
      # is hacking and knows our hash secret?)
      return None

    return uid
  return None

# methods for dealing with cookies

def hash_str(s):
  return hashlib.md5(s+SECRET).hexdigest()

def gen_cookie(uid):
  return str(uid) + "|" + hash_str(str(uid))

def check_cookie(cookie):
  parts = cookie.split('|')
  if len(parts) != 2: 
    return False
  if hash_str(parts[0]) == parts[1]:
    return True
  return False

def get_uid(cookie):
  parts = cookie.split('|')
  if len(parts) != 2: 
    return None
  return int(parts[0])

# login/signup form validations

def valid_username(username):
  return USER_RE.match(username)

def valid_password(password):
  return PASSWORD_RE.match(password)

def valid_verify(verify, password):
  return verify == password

def valid_email(email):
  return email == '' or EMAIL_RE.match(email)