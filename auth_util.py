# authutil.py
# This is a module that contains useful functions for authorization (login/signup)
# that are independent of the main webpage flow.

import re
import hashlib

# cookie hash secret
SECRET = 'linenoise'

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^^[\S]+@[\S]+\.[\S]+$$")

# methods for dealing with cookies

"""
# authenticates cookie cookie and returns the corresponding
# user
def authenticate(handler):
  # first check if the cookie is valid
  auth = self.request.cookies.get('auth', '')
  if check_cookie(auth):
    # then check if the user actually exists
    uid = get_uid(cookie)
    return User.get_by_id(uid) 
"""

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