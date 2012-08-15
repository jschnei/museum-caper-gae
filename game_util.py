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


VALID_COLORS = set(['blue',
                    'brown',
                    'green',
                    'purple',
                    'red',
                    'yellow'])

def piece_file(color):
  if color in VALID_COLORS:
    return 'pieces/{}.png'.format(color)
  else:
    raise Exception('Invalid color!')

class Character(Piece):
  def __init__(self, pos_x, pos_y, color, uid):
    super(Character, self).__init__(pos_x, pos_y, piece_file(color))
    self.color = color
    self.uid = uid


class Painting(Piece):
  def __init__(self):
    # insert later
    return

class Lock(Piece):
  def __init__(self):
    # insert later
    return

