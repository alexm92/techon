import sys
import json
from copy import deepcopy

from models.game import Bug, Tower, Shoot, GameException


class GameHandler(object):
    def __init__(self, inputFile=None, outputFile=None):
        self.inputFile = inputFile
        self.outputFile = outputFile

        self.life = 0
        self.money = 0
        self.towerRange = 0
        self.towerCost = 0
        self.reward = 0

        self.colors = []
        self.towers = {}
        self.bugs = {}
        self.table = []
        self.actions = []
        self.road = {}
        self.bestTowerPositions = []

        self._readInputFile()
        self._buildRoad()
        self._getBestTowerPositions()

    def _readInputFile(self):
        with open(self.inputFile, 'r') as f:
            section = 0
            for line in f:
                if line == '\n':
                    section += 1
                    continue

                if section == 0:
                    self.__readVars(line)
                elif section == 1:
                    self.__readBug(line)
                else:
                    self.__readTable(line)

    def __readVars(self, line):
        if 'life' in line:
            self.life = int(line.split('=')[-1])
        elif 'money' in line:
            self.money = int(line.split('=')[-1])
        elif 'range' in line:
            self.towerRange = int(line.split('=')[-1])
        elif 'cost' in line:
            self.towerCost = int(line.split('=')[-1])
        elif 'reward' in line:
            self.reward = int(line.split('=')[-1])

    def __readBug(self, line):
        line = line.split()
        bugName, colorsList, frame = line[0], line[1 : -1], line[-1]
        frame = int(frame.split('=')[-1])

        bug = Bug(name=bugName, frame=frame)
        for color in colorsList:
            colorName, value = color.split('=')
            bug.colors[colorName] = int(value)
            
            # add color to list
            self.colors.append(colorName)

        self.bugs[bug.name] = bug

    def __readTable(self, line):
        if 'E' in line:
            x = len(self.table)
            y = line.split().index('E')
            self.road[(None, None)] = (x, y)

        self.table.append(line.split())

    def _buildRoad(self, start=(None, None)):
        start = self.road[start]
        dx = [-1, 1, 0, 0]
        dy = [0, 0, 1, -1]

        for x, y in zip(dx, dy):
            try:
                if (self.table[start[0] + x][start[1] + y] in '1X' and 
                    (start[0] + x, start[1] + y) not in self.road
                ):
                    
                    self.road[start] = (start[0] + x, start[1] + y)
                    self._buildRoad(start)
            except IndexError:
                pass
        

    def _readOutputFile(self):
        with open(self.outputFile, 'r') as f:
            action = None
            tower = None
            shoot = None

            for line in f:
                if len(line) <= 5:
                    if tower:
                        self.towers[tower.name] = tower
                        self.actions.append(tower)
                    elif shoot:
                        self.actions.append(shoot)

                    tower = None
                    shoot = None
                    action = None
                    continue
                elif 'action' in line:
                    action = line.split('=')[-1].strip()
                    if action == 'new_tower':
                        tower = Tower()
                    else:
                        shoot = Shoot()
                    continue

                if 'frame' in line:
                    frame = int(line.split('=')[-1])
                    if tower:
                        tower.frame = frame
                    else:
                        shoot.frame = frame
                    continue

                if action == 'new_tower':
                    if 'name' in line:
                        tower.name = line.split('=')[-1].strip()
                        continue
                    elif 'position' in line:
                        p = [int(x) for x in line.split('=')[-1].split(',')]
                        tower.x = p[1]
                        tower.y = p[0]
                        continue
                    elif 'colors' in line:
                        colorsList = line.split('=')[-1].split(',')
                        for color in colorsList:
                            name, value = color.split(':')
                            tower.colors[name] = int(value)
                        continue
                   

                elif action == 'shoot':
                    if 'tower_name' in line:
                        shoot.towerName = line.split('=')[-1].strip()
                        continue
                    elif 'bug_name' in line:
                        shoot.bugName = line.split('=')[-1].strip()
                        continue

            if tower:
                self.towers[tower.name] = tower
                self.actions.append(tower)
            elif shoot:
                self.actions.append(shoot)

    def _getBestTowerPositions(self):
        towerHit = {}

        for point in self.road.values():
            if self.table[point[0]][point[1]] == 'X':
                continue
            for i in xrange(point[0] - self.towerRange, point[0] + self.towerRange + 1):
                for j in xrange(point[1] - self.towerRange, point[1] + self.towerRange + 1):
                    if 0 <= i and i < len(self.table) and 0 <= j and j < len(self.table[0]) and self.table[i][j] == '0':
                        try:
                            towerHit[(i, j)] += 1
                        except KeyError:
                            towerHit[(i, j)] = 1

        positions = sorted(towerHit.items(), key=lambda item: item[1])
        for position, value in positions:
            self.bestTowerPositions.append(position)


    def printOutput(self):
        with open(self.outputFile, 'w') as f:
            for action in self.actions:
                if isinstance(action, Tower):
                    f.write('action=new_tower\n')
                    f.write('frame=%s\n' % action.frame)
                    f.write('name=tower_%s%s\n' % (action.x, action.y))
                    f.write('position=%s,%s\n' % (action.y, action.x))
                    f.write('colors=%s\n' % ','.join(['%s:%s' % (key, value) for key, value in action.colors.iteritems() if value > 0]))
                elif isinstance(action, Shoot):
                    f.write('action=shoot\n')
                    f.write('frame=%s\n' % action.frame)
                    f.write('tower_name=%s\n' % action.towerName)
                    f.write('bug_name=%s\n' % action.bugName)

                f.write('\n')


    def moveActiveBugs(self, life, frame):
        for _, bug in self.bugs.iteritems():
            if not bug.isAlive or bug.frame > frame:
                continue
            nextPosition = self.road[(bug.x, bug.y)]
            if self.table[nextPosition[0]][nextPosition[1]] != 'X':
                bug.x = nextPosition[0]
                bug.y = nextPosition[1]
            else:        
                life -= bug.life
                if life < 0:
                    raise GameException('Game over at frame #%s' % frame)

        return life

    def executeAction(self, action, life, money, frame):
        if action.frame != frame:
            return life, money

        if isinstance(action, Tower):
            if self.table[action.x][action.y] != '0':
                raise GameException('Tower #%s position is not valid' % action.name)
            if len(action.colors) > 5:
                raise GameException('Tower #%s fires more than 5 colors' % action.name)
            if len(action.name) > 16:
                raise GameException('Tower name has more than 16 chars')
            for color, value in action.colors.iteritems():
                if value > 100000:
                    raise GameException('Tower #%s has big damage: #%s = %s' % (action.name, color, value))
                if value < 0:
                    raise GameException('Tower #%s has negative damage: #%s = %s' % (action.name, color, value))

            # pay for tower
            money -= self.towerCost 
            if money < 0:
                raise GameException('Not enough money for tower #%s' % action.name)

        elif isinstance(action, Shoot):
            # shoot bug
            tower = self.towers[action.towerName]
            bug = self.bugs[action.bugName]

            if max(abs(bug.x - tower.x), abs(bug.y - tower.y)) > self.towerRange:
                raise GameException('Bug #%s is too far from tower #%s' % (bug.name, tower.name))   

            for key, value in tower.colors.iteritems():
                bug.colors[key] -= value

                # check extra damage, and 
                # add money if bug is dead
                if bug.life <= 0:
                    life += bug.life
                    money += self.reward
                    print '#%s extra kill by #%s life=%s, money=%s' % (action.bugName, action.towerName, life, money)

            if life < 0:
                raise GameException('Game over at frame #%s' % frame)

        return life, money


    def nextGameState(self, life, money, frame):
        # move all avtive bugs
        life = self.moveActiveBugs(life, frame)

        # get actions by frame
        actions = self.getActions(life, money, frame)

        # check actions
        for i in xrange(1, len(actions)):
            if (actions[i - 1].frame > actions[i].frame or (
                actions[i - 1].frame == actions[i].frame and 
                isinstance(actions[i - 1], Shoot) and isinstance(actions[i], Tower))
            ):
                raise GameException('Frames are not in order: %s' % i)

        # execute each action
        for action in actions:
            life, money = self.executeAction(action, life, money, frame)

        return life, money, frame + 1

    def getBestTarget(self, tower, life, money, frame):
        for _, bug in self.bugs.iteritems():
            # ignore ig bug is not in frame or dead
            if not bug.isAlive or bug.frame > frame:
                continue

            backupBugs = deepcopy(self.bugs)
            try:
                action = Shoot(frame, tower.name, bug.name)
                self.executeAction(action, life, money, frame)
                return bug
            except GameException:
                pass
            self.bugs = backupBugs

        return None

    def getActions(self, life, money, frame):
        actions = []
        if frame == 0:
            numberOfTowers = 1
            for towerIndex in xrange(numberOfTowers):
                position = self.bestTowerPositions.pop()
                tower = Tower('tower_%s' % towerIndex, 0, position[0], position[1], {'red': 5, 'blue': 0 if towerIndex == 1 else 7})
                self.towers[tower.name] = tower
                actions.append(tower)

        for _, tower in self.towers.iteritems():
            target = self.getBestTarget(tower, life, money, frame)
            if target:
                shoot = Shoot(frame, tower.name, target.name)
                actions.append(shoot)

        return actions


    def generateSolution(self):
        life, money, frame = self.life, self.money, 0

        while True:
            print 'Frame:', frame
            print '-------------'
            life, money, frame = self.nextGameState(life, money, frame)
            print 'life=%s money=%s' % (life, money)


    def test(self, fromFile=False):
        backupMoney = deepcopy(self.money)
        backupLife = deepcopy(self.life)
        backupBugs = deepcopy(self.bugs)

        if fromFile:
            self._readOutputFile()

        for i in xrange(1, len(self.actions)):
            if (self.actions[i - 1].frame > self.actions[i].frame or (
                self.actions[i - 1].frame == self.actions[i].frame and 
                isinstance(self.actions[i - 1], Shoot) and isinstance(self.actions[i], Tower))
            ):
                raise GameException('Frames are not in order: %s' % i)

        frame = 0
        while True:
            print 'Frame: ', frame
            print '-----------------'

            for bugName, bug in self.bugs.iteritems():
                if not bug.isAlive or bug.frame > frame:
                    continue
                nextPosition = self.road[(bug.x, bug.y)]
                if self.table[nextPosition[0]][nextPosition[1]] != 'X':
                    bug.x = nextPosition[0]
                    bug.y = nextPosition[1]
                else:        
                    self.life -= bug.life

            for action in self.actions:
                if action.frame < frame:
                    continue
                if action.frame > frame:
                    break

                if isinstance(action, Tower):
                    print action

                    if self.table[action.x][action.y] != '0':
                        raise GameException('Tower #%s position is not valid' % action.name)
                    if len(action.colors) > 5:
                        raise GameException('Tower #%s fires more than 5 colors' % action.name)
                    if len(action.name) > 16:
                        raise GameException('Tower name has more than 16 chars')
                    for color, value in action.colors.iteritems():
                        if value > 100000:
                            raise GameException('Tower #%s has big damage: #%s = %s' % (action.name, color, value))
                        if value < 0:
                            raise GameException('Tower #%s has negative damage: #%s = %s' % (action.name, color, value))

                    # pay for tower
                    self.money -= self.towerCost 
                    if self.money < 0:
                        raise GameException('Not enough money for tower #%s' % action.name)

                elif isinstance(action, Shoot):
                    # shoot bug
                    tower = self.towers[action.towerName]
                    bug = self.bugs[action.bugName]

                    print action, '~>', bug

                    if max(abs(bug.x - tower.x), abs(bug.y - tower.y)) > self.towerRange:
                        raise GameException('Bug #%s is too far from tower #%s' % (bug.name, tower.name))   

                    for key, value in tower.colors.iteritems():
                        bug.colors[key] -= value

                        # check extra damage, and 
                        # add money if bug is dead
                        if bug.life <= 0:
                            self.life += bug.life
                            self.money += self.reward
                            print '#%s extra kill by #%s life=%s, money=%s' % (action.bugName, action.towerName, self.life, self.money)

                    if self.life < 0:
                        raise GameException('Game over at frame #%s' % frame)

            # end of actions
            if frame == self.actions[-1].frame:
                break
            
            print 'Frame=%s Money=%s Life=%s\n' % (frame, self.money, self.life)
            frame += 1

        data = (deepcopy(self.life), deepcopy(self.money))
        
        self.life = backupLife
        self.money = backupMoney
        self.bugs = backupBugs

        return data


    def __repr__(self):
        return json.dumps(vars(self))

    def __str__(self):
        return json.dumps(vars(self))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'No input file'
    else:
        inputFile = '%s' % sys.argv[1]
        outputFile = 'output/%s' % sys.argv[1].split('/')[-1]
        
        game = GameHandler(inputFile=inputFile, outputFile=outputFile)

        game.generateSolution()

        #game.findSolution()
        #game.printOutput()

        # print game.test()
        # print vars(game)

