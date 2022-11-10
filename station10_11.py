

# robot program times
robot_prog_times = {'pick': 0.95,
                    'inspect': 1.0,
                    'place': 0.95}

shuttle_duration = 0.25

# Verbosity:
# ______________________
# 0: None
# 1: All
verbose = 0


# define the Feeder class
class Feeder(object):
    def __init__(self):
        self.position = 'ST11'
        self.st10_nest_parts = True
        self.st11_nest_parts = True
        self.shuttle_duration = shuttle_duration + robot_prog_times.get('pick')
        self.shuttle_start = 0
        self.in_cycle = False

    def shuttle(self, time):
        self.in_cycle = True
        self.shuttle_start = time

    def check_status(self, time):
        if self.in_cycle:
            if self.shuttle_start + self.shuttle_duration < time:
                self.in_cycle = False
                self.shuttle_start = 0
                if self.position == 'ST10':
                    self.position = 'ST11'
                    self.st10_nest_parts = True
                elif self.position == 'ST11':
                    self.position = 'ST10'
                    self.st11_nest_parts = True
        elif self.position == 'ST10' and not self.st10_nest_parts:
            self.shuttle(time)
            if verbose == 1:
                print("{0:6.2f}".format(time + robot_prog_times.get('pick')), 'Shuttle start to ST11')
        elif self.position == 'ST11' and not self.st11_nest_parts:
            self.shuttle(time)
            if verbose == 1:
                print("{0:6.2f}".format(time + robot_prog_times.get('pick')), 'Shuttle start to ST10')


# define the Robot class
class Robot(object):
    def __init__(self, name):
        self.name = name
        self.current_prog = None
        self.prog_time_start = 0
        self.prog_cycle_time = 0
        self.in_cycle = False
        self.part_present = False
        self.part_inspected = False
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
        if prog == 'place':
            self.start_cycle_clock = time

    # Retrieve current state of robot
    def check_status(self, time):
        if self.in_cycle and (self.prog_time_start + self.prog_cycle_time < time):
            self.in_cycle = False
            if self.current_prog == 'pick':
                self.part_present = True
            elif self.current_prog == 'inspect':
                self.part_inspected = True
                self.end_cycle_clock = time
                if self.start_cycle_clock != 0:
                    self.cycle_times.append(self.end_cycle_clock - self.start_cycle_clock)
            elif self.current_prog == 'place':
                self.part_present = False
                self.part_inspected = False
                self.process_complete = True
            self.current_prog = None
        return self.in_cycle


def initialize():
    # initial conditions
    st10_handling = Robot('ST10 Handling')
    st11_handling = Robot('ST11 Handling')
    st10_11_feeder = Feeder()
    return st10_handling, st11_handling, st10_11_feeder


def status_check(time, handling, feeder):
    handling.check_status(time)
    feeder.check_status(time)


def decision_tree(time, handling, feeder, station):
    if not handling.in_cycle:
        if not handling.part_present:
            if handling.name == 'ST10 Handling' and feeder.position == 'ST10' and feeder.st10_nest_parts:
                handling.start_cycle(time, 'pick')
                feeder.st10_nest_parts = False
                if verbose == 1:
                    print("{0:6.2f}".format(time), handling.name + ' Picking Part')
            if handling.name == 'ST11 Handling' and feeder.position == 'ST11' and feeder.st11_nest_parts:
                handling.start_cycle(time, 'pick')
                feeder.st11_nest_parts = False
                if verbose == 1:
                    print("{0:6.2f}".format(time), handling.name + ' Picking Part')
        elif not handling.part_inspected:
            handling.start_cycle(time, 'inspect')
            if verbose == 1:
                print("{0:6.2f}".format(time), handling.name + ' Inspecting Part')
        elif handling.part_inspected and station.current_pallet and not station.process_complete:
            handling.start_cycle(time, 'place')
            if verbose == 1:
                print("{0:6.2f}".format(time), handling.name + ' Placing at Pallet fixture')



