import random

# assumptions
pick_prob = 0.45
total_qty_min = 2
feed_in_qty_min = 5
feed_in_qty_max = 10
inspect_duration = 0.25
shuffle_duration = 1.5
feed_in_duration = 2.0

# robot program times
robot_prog_times = {'pick left feeder': 0.88,
                    'pick right feeder': 0.88,
                    'place at pallet': 1.54}

# camera assignments
cameras = {'ST14a Left Feeder': 1,
           'ST14a Right Feeder': 2,
           'ST14b Left Feeder': 3,
           'ST14b Right Feeder': 4}

# Verbosity:
# ______________________
# 0: None
# 1: All
# 2: Robots
# 3: STA14a Left Feeder
# 4: STA14a Right Feeder
# 6: STA14b Left Feeder
# 7: STA14b Right Feeder
# 8: Vision Controller
verbose = 0


# define the Feeder class
class Feeder(object):
    def __init__(self, name):
        self.name = name
        self.inspect_in_cycle = False
        self.shuffle_in_cycle = False
        self.feedin_in_cycle = False
        self.pick_in_cycle = False
        self.ready_for_pick = False
        self.ready_for_inspect = False
        self.total_qty_min = total_qty_min
        self.feedin_qty_min = feed_in_qty_min
        self.feedin_qty_max = feed_in_qty_max
        self.total_qty = 0
        self.pick_qty = 0
        self.pick_prob = pick_prob
        self.inspect_duration = inspect_duration
        self.shuffle_duration = shuffle_duration
        self.feedin_duration = feed_in_duration
        self.pick_duration = robot_prog_times.get('pick left feeder')
        self.inspect_start = 0
        self.shuffle_start = 0
        self.feedin_start = 0
        self.pick_start = 0

    # action: trigger vision inspection
    def inspect(self, time):
        self.inspect_in_cycle = True
        self.inspect_start = time
        if (verbose == 1 or
                (self.name == 'ST14 Left Feeder' and verbose == 3) or
                (self.name == 'ST14 Right Feeder' and verbose == 4) or
                (self.name == 'ST15 Left Feeder' and verbose == 6) or
                (self.name == 'ST15 Right Feeder' and verbose == 7)):
            print("{0:6.2f}".format(time), self.name + ' Inspecting')

    # action: shuffle parts currently in the tray
    def shuffle(self, time):
        self.shuffle_in_cycle = True
        self.shuffle_start = time
        self.pick_qty = sum(random.choices([1, 0], [self.pick_prob, 1 - self.pick_prob], k=self.total_qty))
        if (verbose == 1 or
                (self.name == 'ST14 Left Feeder' and verbose == 3) or
                (self.name == 'ST14 Right Feeder' and verbose == 4) or
                (self.name == 'ST15 Left Feeder' and verbose == 6) or
                (self.name == 'ST15 Right Feeder' and verbose == 7)):
            print("{0:6.2f}".format(time), self.name + ' Shuffling ' + str(self.total_qty) + ' parts')

    # action: add more parts to the tray and shuffle
    def feed_in(self, time):
        self.feedin_in_cycle = True
        self.feedin_start = time
        feed_qty = random.randint(self.feedin_qty_min, self.feedin_qty_max)
        self.total_qty += feed_qty
        if (verbose == 1 or
                (self.name == 'ST14 Left Feeder' and verbose == 3) or
                (self.name == 'ST14 Right Feeder' and verbose == 4) or
                (self.name == 'ST15 Left Feeder' and verbose == 6) or
                (self.name == 'ST15 Right Feeder' and verbose == 7)):
            print("{0:6.2f}".format(time), self.name + ' Feeding in ' + str(feed_qty) + ' parts')

    # action: remove one pick-able part from the tray
    def pick(self, time):
        self.pick_in_cycle = True
        self.ready_for_pick = False
        self.pick_start = time
        self.pick_qty -= self.pick_qty
        self.total_qty -= self.total_qty

    # retrieve current status of the Feeder
    def check_status(self, time, vision):
        # update 'in cycle' statuses
        if self.inspect_in_cycle and (self.inspect_start + self.inspect_duration < time):
            self.inspect_in_cycle = False
            self.inspect_start = 0
        if self.shuffle_in_cycle and (self.shuffle_start + self.shuffle_duration < time):
            self.shuffle_in_cycle = False
            self.shuffle_start = 0
            self.ready_for_inspect = True
        if self.feedin_in_cycle and (self.feedin_start + self.feedin_duration < time):
            self.feedin_in_cycle = False
            self.feedin_start = 0
            self.shuffle(time)
        if self.pick_in_cycle and (self.pick_start + self.pick_duration < time):
            self.pick_in_cycle = False
            self.pick_start = 0
            self.ready_for_inspect = True

        # check if tray has a pick-able part and shuffle/feed-in as necessary
        if not self.inspect_in_cycle and \
                not self.shuffle_in_cycle and \
                not self.feedin_in_cycle and \
                not self.pick_in_cycle:
            if self.ready_for_inspect:
                if not vision.in_cycle:
                    self.inspect(time)
                    vision.start_inspection(time, cameras.get(self.name))
                    self.ready_for_inspect = False
            else:
                if self.pick_qty > 0:
                    self.ready_for_pick = True
                elif self.total_qty < self.total_qty_min:
                    self.feed_in(time)
                else:
                    self.shuffle(time)


# define the Robot class
class Robot(object):
    def __init__(self, name):
        self.name = name
        self.current_prog = None
        self.prog_time_start = 0
        self.prog_cycle_time = 0
        self.in_cycle = False
        self.part_present = False
        self.process_complete = False
        self.location = ''
        self.start_cycle_clock = 0
        self.end_cycle_clock = 0
        self.cycle_times = []

    # Give the robot a canned task to complete
    def start_cycle(self, time, prog):
        self.current_prog = prog
        self.prog_time_start = time
        self.prog_cycle_time = robot_prog_times.get(prog)
        self.in_cycle = True
        if prog == 'place at pallet':
            self.start_cycle_clock = time

    # Retrieve current state of robot
    def check_status(self, time):
        if self.in_cycle and (self.prog_time_start + self.prog_cycle_time < time):
            self.in_cycle = False
            if self.current_prog == 'pick left feeder' or self.current_prog == 'pick right feeder':
                self.part_present = True
                self.end_cycle_clock = time
                if self.start_cycle_clock != 0:
                    self.cycle_times.append(self.end_cycle_clock - self.start_cycle_clock)
            elif self.current_prog == 'place at pallet':
                self.part_present = False
                self.process_complete = True
            self.current_prog = None
        return self.in_cycle


# define the Vision Controller class
class VisionController(object):
    def __init__(self):
        self.in_cycle = False
        self.active_camera = 0
        self.inspect_start = 0
        self.inspect_duration = inspect_duration

    # action: run inspection program on a single camera
    def start_inspection(self, time, camera):
        self.in_cycle = True
        self.active_camera = camera
        self.inspect_start = time
        if verbose == 1 or verbose == 8:
            print("{0:6.2f}".format(time), 'Inspecting with Camera ' + str(camera))

    # retrieve current status of the Vision Controller
    def check_status(self, time):
        if self.in_cycle and (self.inspect_start + self.inspect_duration < time):
            self.in_cycle = False
            self.inspect_start = 0
            self.active_camera = 0


def initialize():
    # initial conditions
    l_feed_14a = Feeder('ST14a Left Feeder')
    r_feed_14a = Feeder('ST14a Right Feeder')
    l_feed_14b = Feeder('ST14b Left Feeder')
    r_feed_14b = Feeder('ST14b Right Feeder')
    vision = VisionController()
    robot_14a = Robot('ST14a Robot')
    robot_14b = Robot('ST14b Robot')
    return l_feed_14a, r_feed_14a, robot_14a, l_feed_14b, r_feed_14b, robot_14b, vision


def status_check(time, l_feed, r_feed, robot, vision):
    l_feed.check_status(time, vision)
    r_feed.check_status(time, vision)
    robot.check_status(time)
    vision.check_status(time)


def decision_tree(time, l_feed, r_feed, robot, station):
    # robot's decision tree
    if not robot.in_cycle:
        if not robot.part_present:
            if l_feed.ready_for_pick:
                robot.start_cycle(time, 'pick left feeder')
                l_feed.pick(time)
                if verbose == 1 or verbose == 2:
                    print("{0:6.2f}".format(time), robot.name + ' Picking from Left Feeder')
            elif r_feed.ready_for_pick:
                robot.start_cycle(time, 'pick right feeder')
                r_feed.pick(time)
                if verbose == 1 or verbose == 2:
                    print("{0:6.2f}".format(time), robot.name + ' Picking from Right Feeder')
        else:
            if station.current_pallet and not station.process_complete:
                robot.start_cycle(time, 'place at pallet')
                if verbose == 1 or verbose == 2:
                    print("{0:6.2f}".format(time), robot.name + ' Placed at Pallet fixture')
