import sys
from copy import deepcopy

from models.game import Tower, Bug

LIFE = 0
MONEY = 0
TOWER_RANGE = 0
TOWER_COST = 0
REWARD_PER_BUG = 0

COLORS = set()
BUGS = {}
TOWERS = {}

TABLE = []

def read_vars(line):
    global LIFE, MONEY, TOWER_RANGE, TOWER_COST, REWARD_PER_BUG

    if 'life' in line:
        LIFE = int(line.split('=')[-1])
    elif 'money' in line:
        MONEY = int(line.split('=')[-1])
    elif 'range' in line:
        TOwER_RANGE = int(line.split('=')[-1])
    elif 'cost' in line:
        TOWER_COST = int(line.split('=')[-1])
    elif 'reward' in line:
        REWARD_PER_BUG = int(line.split('=')[-1])

def read_bug(line):
    global BUGS, COLORS

    line = line.split()
    bug_name, colors_list, frame = line[0], line[1 : -1], line[-1]
    frame = int(frame.split('=')[-1])

    BUGS[bug_name] = {'frame': frame}
    for color in colors_list:
        name, value = color.split('=')
        BUGS[bug_name][name] = int(value)
        COLORS.add(name)

def read_table(line):
    global TABLE
    TABLE.append(line.split())

def read_data(input_file):
    with open(input_file, 'r') as f:
        section = 0
        for line in f:
            if line == '\n':
                section += 1
                continue

            if section == 0:
                read_vars(line)
            elif section == 1:
                read_bug(line)
            else:
                read_table(line)

    #print BUGS
    #print COLORS
    #print TABLE 
    
def check_output(output_file):
    global LIFE, MONEY, BUGS, TOWERS

    last_frame = 0

    with open(output_file, 'r') as f:
        action = None
        tower = {}
        shoot = {}

        for line in f:
            if line == '\n':
                tower = {}
                action = None
                continue
            elif 'action' in line:
                action = line.split('=')[-1].strip()
                continue

            if action == 'new_tower':
                if 'frame' in line:
                    tower['frame'] = int(line.split('=')[-1])
                    continue
                elif 'name' in line:
                    tower['name'] = line.split('=')[-1].strip()
                    continue
                elif 'position' in line:
                    p = [int(x) for x in line.split('=')[-1].split(',')]
                    tower['position'] = {'x': p[1], 'y': p[0]}
                    continue
                elif 'colors' in line:
                    colors_list = line.split('=')[-1].split(',')
                    tower['colors'] = {}
                    for color in colors_list:
                        name, value = color.split(':')
                        tower['colors'][name] = int(value)
                    continue

                if tower['frame'] < last_frame:
                    raise Exception('Frames are not in order. Current frame is %s and last is %s' % (tower['frame'], last_frame))
                if TABLE[tower['position']['x']][tower['position']['y']] != '0':
                    raise Exception('Tower #%s position is not valid' % tower['name'])
                if len(tower['colors']) > 5:
                    raise Exception('Tower #%s fires more than 5 colors' % tower['name'])
                if len(tower['name']) > 16:
                    raise Exception('Tower name has more than 16 chars')
                for color, value in tower['colors'].iteritems():
                    if value > 100000:
                        raise Exception('Tower #%s has big damage: #%s = %s' % (tower['name'], color, value))
                    if value < 0:
                        raise Exception('Tower #%s has negative damage: #%s = %s' % (tower['name'], color, value))
                
                last_frame = tower['frame']

                # pay for tower
                MONEY -= TOWER_COST 
                if MONEY < 0:
                    raise Exception('Not enough money for tower #%s' % tower['name'])


                # add tower
                TOWERS[tower['name']] = deepcopy(tower)

            elif action == 'shoot':
                if 'frame' in line:
                    shoot['frame'] = int(line.split('=')[-1])
                    continue
                elif 'tower_name' in line:
                    shoot['tower_name'] = line.split('=')[-1].strip()
                    continue
                elif 'bug_name' in line:
                    shoot['bug_name'] = line.split('=')[-1].strip()

                if shoot['frame'] < last_frame:
                    raise Exception('Frames are not in order. Current frame is %s and last is %s' % (tower['frame'], last_frame))
                if shoot['bug_name'] not in BUGS:
                    raise Exception('Bug #%s does not exist.' % shoot['bug_name'])
                if shoot['tower_name'] not in TOWERS:
                    raise Exception('Tower #%s does not exist' % shoot['tower_name'])
               
                # shoot bug
                tower = TOWERS[shoot['tower_name']]
                bug = BUGS[shoot['bug_name']]
                for key, value in tower.iteritems():
                    if key in COLORS:
                        bug[key] -= tower[key]

                        # check extra damage
                        if bug[key] < 0:
                            LIFE += bug[key]

                if LIFE < 0:
                    raise Exception('Game over')

                last_frame = shoot['frame']
                # print shoot

    # print TOWERS
    print LIFE, MONEY

def main():
    if len(sys.argv) == 0:
        print 'No input file'
    else:
        input_file = 'input/%s' % sys.argv[1]
        output_file = 'output/%s' % sys.argv[1]

        read_data(input_file)
        check_output(output_file)

if __name__ == '__main__':
    main()

