import game_util

def load_map(mapfile, pieces):
  m = Map()
  m.static = load_static_map(mapfile)
  m.dynamic = load_dynamic_map(pieces)
  return m

def load_static_map(fname):
  with open('maps/%s' % fname) as f:
    line = f.readline()
    dims = [int(x) for x in line.split()]
    m = StaticMap(dims[0], dims[1])

    for y in xrange(dims[1]):
      line = f.readline()
      vals = [int(x) for x in line.split()]
      for x in xrange(dims[0]):
        m.set_cell(x, y, vals[x])

  return m

def load_dynamic_map(pieces):
  m = DynamicMap()
  for piece in pieces:
    m.data[piece.position] = piece

  return m

# Map class. Stores both the static map and the dynamic map
class Map(object):
  def __init__(self):
    self.static = None
    self.dynamic = None


  def get_cell_images(self):
    cell_images = { }
    for pos, val in self.static.data.items():
      if pos in self.dynamic.data:
        cell_images[pos] = self.dynamic.data[pos].img_file
      else:
        cell_images[pos] = StaticMap.CELL_IMG % val

    return cell_images


  def valid_move(self, piece, direction):
    return (self.static.valid_move(piece.position, direction) and
            self.dynamic.valid_move(piece, direction))
  
  def valid_placement(self, position):
    return (self.static.valid_placement(position) and
            self.dynamic.valid_placement(position))



# StaticMap class for storing the static map
class StaticMap(object):
  CELL_IMG = 'cell%i.png'

  def __init__(self, width, height):
    self.width = width
    self.height = height

    # the static map is stored as a dict where 
    # data[(x, y)] is the map cell at coordinates
    # (x, y)
	
    self.data = dict([((x, y), 0) for x in xrange(self.width) 
                                  for y in xrange(self.height)])

  # set cell x, y to cell_val
  def set_cell(self, x, y, cell_val):
    self.data[(x,y)] = cell_val

  def valid_move(self, start_pos, direction):
    dir_map = {(0,-1): 1, (1, 0): 2, (0, 1): 4, (-1, 0): 8}
    dir_bit = dir_map[direction]
    if (dir_bit & self.data[start_pos]):
      return False
    else:
      return True
    
  def valid_placement(self, pos):
    # 15 represents a filled square, so
    # we just check that it's not 15.
    return (self.data[pos] != 15)


# DynamicMap class for storing map information about pieces that
# can move/change/aren't always in the same place

class DynamicMap(object):
  def __init__(self):
    # we don't really care about storing width/height
    # information for our dynamic map
    self.data = {}

  def set_cell(self, x, y, piece):
    self.data[(x,y)] = piece

  def valid_move(self, piece, direction):
    new_pos = (piece.position[0] + direction[0],
               piece.position[1] + direction[1])
    # TODO: make more accurate (i.e. thieves can move onto locks and
    # paintings, etc.)
    return self.valid_placement(new_pos)
  
  def valid_placement(self, pos):
    return (pos not in self.data)
    
  




