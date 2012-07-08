# Map class for storing the static map
class Map(object):
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


# load map from file
def load_from_file(fname):
  with open('maps/%s' % fname) as f:
    line = f.readline()
    dims = [int(x) for x in line.split()]
    m = Map(dims[0], dims[1])

    for y in xrange(dims[1]):
      line = f.readline()
      vals = [int(x) for x in line.split()]
      for x in xrange(dims[0]):
        m.set_cell(x, y, vals[x])

  return m





