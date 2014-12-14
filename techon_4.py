import sys
import os
import json
from copy import deepcopy
from random import randrange

from models.game import Bug, Tower, Shoot, GameException


class GameHandler(object):
    def __init__(self, inputFile=None, outputFile=None):
        self.inputFile = inputFile
        self.outputFile = outputFile

        try:
            os.remove(self.outputFile)
        except:
            pass

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

        # add road to each bug
        for _, bug in self.bugs.iteritems():
            bug.road = deepcopy(self.road)

    def __repr__(self):
        return json.dumps(vars(self))

    def __str__(self):
        return json.dumps(vars(self))

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


    def printOutput(self, actions):
        with open(self.outputFile, 'a') as f:
            for action in actions:
                if isinstance(action, Tower):
                    f.write('action=new_tower\n')
                    f.write('frame=%s\n' % action.frame)
                    f.write('name=%s\n' % (action.name))
                    f.write('position=%s,%s\n' % (action.y, action.x))
                    f.write('colors=%s\n' % ','.join(['%s:%s' % (key, value) for key, value in action.colors.iteritems() if value > 0]))
                elif isinstance(action, Shoot):
                    f.write('action=shoot\n')
                    f.write('frame=%s\n' % action.frame)
                    f.write('tower_name=%s\n' % action.towerName)
                    f.write('bug_name=%s\n' % action.bugName)

                f.write('\n')

    def shootBug(self, tower, bug, do_damage):
        colateral = 0
        bugLife = bug.life
        for color, value in tower.colors.iteritems():
            new_value = bug.colors.get(color, 0) - value
            if new_value < 0:
                colateral -= new_value
                new_value = 0
            bugLife -= bug.colors.get(color, 0) - new_value
            if do_damage:
                bug.colors[color] = new_value

        if not do_damage:
            return colateral, bugLife
        return colateral

    def bestTarget(self, tower, backupBugs, life, frame):
        target = None
        maxSavedLife = 0

        for _, bug in backupBugs.iteritems():
            # if bug is dead or not in game, continue
            if not bug.isAlive or bug.frame > frame:
                continue

            if max(abs(bug.x - tower.x), abs(bug.y - tower.y)) > self.towerRange or bug.stepsLeft == 0:
                continue

            lifeBeforeShot = bug.life
            colateral, lifeAfterShot = self.shootBug(tower, bug, False)
            if colateral > 0: #life
                continue


            if lifeBeforeShot - lifeAfterShot - colateral > maxSavedLife:
                target = bug
                maxSavedLife = lifeBeforeShot - bug.life - colateral

            # if bug is in range of tower, pick the closest to end of road
            # if tower.distanceTo(bug) < self.towerRange:
            #    if target is None or target.stepsLeft > bug.stepsLeft:
            #        pass

        return target

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

        elif isinstance(action, Shoot):
            # shoot bug
            tower = self.towers[action.towerName]
            bug = self.bugs[action.bugName]

            if max(abs(bug.x - tower.x), abs(bug.y - tower.y)) > self.towerRange:
                raise GameException('Bug #%s is too far from tower #%s' % (bug.name, tower.name))   

            colateral = self.shootBug(tower, bug, True)

            if colateral > 0:
                life -= colateral
                print '#%s extra kill by #%s life=%s, money=%s' % (action.bugName, action.towerName, life, money)

            if bug.life == 0:
                money += self.reward
                print 'Bug #%s was killed by tower #%s' % (action.bugName, action.towerName)

            print 'Bug #{0} was shot.'.format(bug.name), vars(bug)

        return life, money 

    def nextGameState(self, actions, life, money, frame):
        bugsToRemove = []

        # move active bugs
        for _, bug in self.bugs.iteritems():
            if not bug.isAlive:
                continue

            try:
                bug.move(frame)
            except KeyError:
                life -= bug.life
                print 'Bug #%s got to X with life=%s: %s' % (bug.name, bug.life, bug.colors)
                bugsToRemove.append(bug.name)

        for bugName in bugsToRemove:
            self.bugs.pop(bugName)

        for action in actions:
            life, money = self.executeAction(action, life, money, frame)

        return life, money

    def findSolution(self):
        frame = 0
        life = self.life
        money = self.money

        actions = [
            ## Map 1
            # Tower('tower_0', 0, 1, 3, {'red': 40, 'blue': 0}),
            # Tower('tower_1', 0, 2, 5, {'red': 33, 'blue': 0}),
            # Tower('tower_2', 0, 3, 2, {'red': 36, 'blue': 0}),
            # Tower('tower_3', 0, 0, 3, {'red': 11, 'blue': 7}),
            # Tower('tower_4', 0, 1, 1, {'red': 37, 'blue': 14}),

            ## Map 2
            Tower('tower_0', 0, 5, 5, self.bugs['B1'].colors),
            Tower('tower_1', 0, 7, 5, self.bugs['B2'].colors),
            Tower('tower_2', 0, 5, 4, self.bugs['B3'].colors),
            Tower('tower_3', 0, 6, 4, self.bugs['B4'].colors),
            Tower('tower_4', 0, 7, 3, self.bugs['B5'].colors),

        ]

        # numberOfTowers = 4
        # for i in xrange(numberOfTowers):
        #    t = Tower('tower_%s' % i, 0, self.bestTowerPositions[-i - 1][0], self.bestTowerPositions[-i - 1][1], {'red': randrange(0, 1600), 'blue': randrange(0, 600)})
        #    actions.append(t)


        for tower in actions:
            self.towers[tower.name] = tower

        lastFrame = 0
        for _, bug in self.bugs.iteritems():
            if lastFrame < bug.frame:
                lastFrame = bug.frame

        for frame in xrange(len(self.road) + lastFrame + 1):
            print '---------------------------- FRAME {0} ----------------------'.format(frame)

            backupBugs = deepcopy(self.bugs)
            for _, bug in backupBugs.iteritems():
                try:
                    bug.move(frame) 
                except KeyError:
                    bug.colors = {}

            for _, tower in self.towers.iteritems():
                target = self.bestTarget(tower, backupBugs, life, frame)
                if target:
                    self.shootBug(tower, target, True)

                    shoot = Shoot(frame, tower.name, target.name)
                    actions.append(shoot)
                    # print vars(target)

            if frame == 74:
                actions = []
                t = Tower('tower_5', frame, 6, 3, self.bugs['B6'].colors)
                actions.append(t)
                self.towers[t.name] = t
                shoot = Shoot(frame, 'tower_5', 'B6')
                actions.append(shoot)
            elif frame == 91:
                actions = []
                t = Tower('tower_6', frame, 7, 6, self.bugs['B7'].colors)
                actions.append(t)
                self.towers[t.name] = t
                shoot = Shoot(frame, 'tower_6', 'B7')
                actions.append(shoot)
            elif frame == 103:
                actions = []
                t = Tower('tower_7', frame, 7, 4, self.bugs['B8'].colors)
                actions.append(t)
                self.towers[t.name] = t
                shoot = Shoot(frame, 'tower_7', 'B8')
                actions.append(shoot)

               

            print actions
            self.printOutput(actions)

            life, money = self.nextGameState(actions, life, money, frame)

            print 'after actions: life={0} money={1}'.format(life, money)

            if life <= 0:
                raise GameException('Game Over. life={0} money={1} frame={2}'.format(life, money, frame))

            actions = []

            print '\n'

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'No input file'
    else:
        inputFile = '%s' % sys.argv[1]
        outputFile = 'output/%s_solution' % sys.argv[1].split('/')[-1]
        
        game = GameHandler(inputFile=inputFile, outputFile=outputFile)

        table = deepcopy(game.table)
        positions = deepcopy(game.bestTowerPositions)
        index = 0
        while len(positions) > 0:
            x, y = positions.pop()
            table[x][y] = 'T%s' % index
            index += 1
        for row in table:
            print '\t'.join(row)

        while True:
            gameCopy = deepcopy(game)
            try:
                print gameCopy.findSolution()
            except GameException as e:
                print e.message
                break
            else:
                print '\n\n\nEvrika!!!!!!!!!!!!!\n\n'
                break

