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

