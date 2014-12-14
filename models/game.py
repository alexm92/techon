import json
from copy import deepcopy

class GameException(Exception):
    pass

class GameObject(object):
    def __init__(self):
        # import ipdb; ipdb.set_trace()
        pass

    def __repr__(self):
        return json.dumps(vars(self))

    def __str__(self):
        return json.dumps(vars(self))

class Tower(GameObject):
    def __init__(self, name=None, frame=None, x=None, y=None, colors=None):
        self.name = name
        self.frame = frame
        self.x = x
        self.y = y
        if colors is None:
            self.colors = {}
        else:
            self.colors = colors

        super(Tower, self).__init__()


class Bug(GameObject):
    def __init__(self, name=None, frame=None, x=None, y=None, colors=None, road=None):
        self.name = name
        self.frame = frame
        self.x = x
        self.y = y
        self.steps = 0
        self.road = deepcopy(road)
        if colors is None:
            self.colors = {}
        else:
            self.colors = colors

        super(Bug, self).__init__()

    @property
    def isAlive(self):
        return self.life > 0

    @property
    def life(self):
        return sum([value for key, value in self.colors.iteritems()])

    def move(self, frame):
        if self.frame > frame:
            return

        position = self.road[(self.x, self.y)]
        self.x = position[0]
        self.y = position[1]
        self.steps += 1

    @property
    def stepsLeft(self):
        return len(self.road) - self.steps
            
class Shoot(GameObject):
    def __init__(self, frame=None, towerName=None, bugName=None):
        self.frame = frame
        self.towerName = towerName
        self.bugName = bugName

        super(Shoot, self).__init__()


