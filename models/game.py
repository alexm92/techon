import json

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
    def __init__(self, name=None, frame=None, x=None, y=None, colors=None):
        self.name = name
        self.frame = frame
        self.x = x
        self.y = y
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
            
class Shoot(GameObject):
    def __init__(self, frame=None, towerName=None, bugName=None):
        self.frame = frame
        self.towerName = towerName
        self.bugName = bugName

        super(Shoot, self).__init__()


class GameState(GameObject):
    def __init__(self, bugs, towers, actions, life, money, frame=0):
        self.bugs = bugs
        self.towers = towers
        self.life = life
        self.money = money
        self.frame = frame

    def next(self):
        self.moveActiveBugs()
