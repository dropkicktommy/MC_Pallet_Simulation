import station2_3
import station8_9
import station10_11
import station14

# position number: (station id, transit time for pallet to arrive at this station)

pallet_positions = {1: ('ST1', 0.51, 2.34),
                    2: ('ST20', 0.44, 2.41),
                    3: ('ST2', 0.56, 0.0),
                    4: ('ST3', 0.5, 0.0),
                    5: ('ST4', 1.5, 1.35),
                    6: ('ST5', 1.5, 1.35),
                    7: ('ST5a', 0.35, 2.5),
                    8: ('ST6', 0.35, 2.5),
                    9: ('ST7', 0.46, 2.39),
                    10: ('ST8', 0.53, 0.0),
                    11: ('ST9', 0.4, 0.0),
                    12: ('ST10', 0.4, 0.0),
                    13: ('ST11', 0.37, 0.0),
                    14: ('ST12', 0.63, 2.22),
                    15: ('ST13', 0.46, 2.39),
                    16: ('Buffer', 2.5, 0.35),
                    17: ('ST14/15', 0.5, 0.0),
                    18: ('ST16', 0.54, 2.31),
                    19: ('ST17', 0.37, 2.48),
                    20: ('ST18', 0.38, 2.47),
                    21: ('ST19', 0.45, 2.4)}
# time (in seconds) after releasing a pallet before the next upstream pallet can be released
pallet_clearing_time = 0.1
# total number of pallets in the system
pallet_count = 20
# simulation runtime (in hours)
runtime = 1
# time-step increment (in seconds)
time_inc = 0.01
# list of stations to print actions for
verbose = [10, 11]

# initialize variables
position = {}
pallet = {}
cycle_clock = 0
prev_cycle_clock = 0
unload_cycle_times = []


# define the Pallet Stop class
class PalletStop(object):
    def __init__(self, position, station_id, upstream_transit_time, cycle_time):
        self.position = position
        self.station_id = station_id
        self.upstream_transit_time = upstream_transit_time
        self.cycle_time = cycle_time
        self.current_pallet = 0
        self.time_in_station = 0
        self.time_without_pallet = 0
        self.process_complete = False

    def release(self, time):
        if int(self.position) in verbose:
            print("{0:6.2f}".format(time), 'releasing pallet', self.current_pallet, 'from', self.station_id)
        pallet[str(self.current_pallet)].release(time)
        self.current_pallet = 0
        self.process_complete = False
        self.time_in_station = 0

    def check_status(self, time):
        if self.current_pallet != 0:
            self.time_in_station += time_inc
            self.time_without_pallet = 0
        else:
            self.time_without_pallet += time_inc


# define the Pallet class
class Pallet(object):
    def __init__(self, pallet_id, init_position):
        self.pallet_id = pallet_id
        self.current_position = init_position
        self.last_position = 0
        self.in_transit = False
        self.transit_start_time = 0

    def release(self, time):
        self.in_transit = True
        self.transit_start_time = time
        self.last_position = self.current_position
        self.current_position = 0

    def check_status(self, time):
        if self.in_transit:
            next_position = self.last_position + 1
            if next_position > len(pallet_positions):
                next_position = 1
            if self.transit_start_time + position[str(next_position)].upstream_transit_time < time:
                self.in_transit = False
                self.transit_start_time = 0
                position[str(next_position)].current_pallet = self.pallet_id
                if int(position[str(next_position)].position) in verbose:
                    print("{0:6.2f}".format(time),
                          'Pallet',
                          position[str(next_position)].current_pallet,
                          'arrived at',
                          position[str(next_position)].station_id)
                self.current_position = next_position


# run the simulation
def run_simulation():
    global prev_cycle_clock
    print('Simulation Running...')

    # initial conditions
    time = 0
    for pos in pallet_positions:
        station_id, transit_time, cycle_time = pallet_positions.get(pos)
        position[str(pos)] = PalletStop(pos, station_id, transit_time, cycle_time)

    for pal in range(1, pallet_count + 1):
        pallet[str(pal)] = Pallet(pal, pal)
        position[str(pal)].current_pallet = pal

    # initialize station 2&3
    l_feed_2, r_feed_2, robot_2, l_feed_3, r_feed_3, robot_3, vision_2_3 = station2_3.initialize()

    # initialize station 8&9
    st8_handling, st9_handling, st8_9_feeder = station8_9.initialize()

    # initialize station 10&11
    st10_handling, st11_handling, st10_11_feeder = station10_11.initialize()

    # initialize station 14
    l_feed_14a, r_feed_14a, robot_14a, l_feed_14b, r_feed_14b, robot_14b, vision_14 = station14.initialize()

    sim_active = True

    while sim_active:
        pallet_status_check(time)
        station2_3.status_check(time, l_feed_2, r_feed_2, robot_2, vision_2_3)
        station2_3.status_check(time, l_feed_3, r_feed_3, robot_3, vision_2_3)
        station8_9.status_check(time, st8_handling, st8_9_feeder)
        station8_9.status_check(time, st9_handling, st8_9_feeder)
        station10_11.status_check(time, st10_handling, st10_11_feeder)
        station10_11.status_check(time, st11_handling, st10_11_feeder)
        station14.status_check(time, l_feed_14a, r_feed_14a, robot_14a, vision_14)
        station14.status_check(time, l_feed_14b, r_feed_14b, robot_14b, vision_14)

        pallet_decision_tree(time, robot_2, robot_3, robot_14a, robot_14b, st8_handling, st9_handling, st10_handling, st11_handling)
        station2_3.decision_tree(time, l_feed_2, r_feed_2, robot_2, position['3'])
        station2_3.decision_tree(time, l_feed_3, r_feed_3, robot_3, position['4'])
        station8_9.decision_tree(time, st8_handling, st8_9_feeder, position['10'])
        station8_9.decision_tree(time, st9_handling, st8_9_feeder, position['11'])
        station10_11.decision_tree(time, st10_handling, st10_11_feeder, position['12'])
        station10_11.decision_tree(time, st11_handling, st10_11_feeder, position['13'])
        station14.decision_tree(time, l_feed_14a, r_feed_14a, robot_14a, position['17'])
        station14.decision_tree(time, l_feed_14b, r_feed_14b, robot_14b, position['17'])

        if prev_cycle_clock != cycle_clock and prev_cycle_clock != 0:
            unload_cycle_times.append(cycle_clock - prev_cycle_clock)
            prev_cycle_clock = cycle_clock
        time += time_inc

        if time > runtime * 3600:
            # print ST2 Robot Cycle Time Data
            print('')
            print('ST2 Robot avg/max cycle time: ' +
                  str(round(sum(robot_2.cycle_times) / len(robot_2.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(robot_2.cycle_times), 3)))
            # print ST3 Robot Cycle Time Data
            print('ST3 Robot avg/max cycle time: ' +
                  str(round(sum(robot_3.cycle_times) / len(robot_3.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(robot_3.cycle_times), 3)))
            # print ST8 Handling Cycle Time Data
            print('ST8 Handling avg/max cycle time: ' +
                  str(round(sum(st8_handling.cycle_times) / len(st8_handling.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(st8_handling.cycle_times), 3)))
            # print ST9 Handling Cycle Time Data
            print('ST9 Handling avg/max cycle time: ' +
                  str(round(sum(st9_handling.cycle_times) / len(st9_handling.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(st9_handling.cycle_times), 3)))
            # print ST10 Handling Cycle Time Data
            print('ST10 Handling avg/max cycle time: ' +
                  str(round(sum(st10_handling.cycle_times) / len(st10_handling.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(st10_handling.cycle_times), 3)))
            # print ST11 Handling Cycle Time Data
            print('ST11 Handling avg/max cycle time: ' +
                  str(round(sum(st11_handling.cycle_times) / len(st11_handling.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(st11_handling.cycle_times), 3)))
            # print ST14a Robot Cycle Time Data
            print('ST14 Robot avg/max cycle time: ' +
                  str(round(sum(robot_14a.cycle_times) / len(robot_14a.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(robot_14a.cycle_times), 3)))
            # print ST14b Robot Cycle Time Data
            print('ST15 Robot avg/max cycle time: ' +
                  str(round(sum(robot_14b.cycle_times) / len(robot_14b.cycle_times), 3)) +
                  ' / ' +
                  str(round(max(robot_14b.cycle_times), 3)))
            # print Overall Cycle Time Data
            print('')
            print('Overall avg/max takt time: ' +
                  str(round(sum(unload_cycle_times) / len(unload_cycle_times), 3)) +
                  ' / ' +
                  str(round(max(unload_cycle_times), 3)))
            sim_active = False
            print('')
            print('Simulation Complete!')


# checks the current status of all pallets
def pallet_status_check(time):
    for pos in position:
        position[pos].check_status(time)
    for pal in pallet:
        pallet[pal].check_status(time)


#
def pallet_decision_tree(time, robot_2, robot_3, robot_14a, robot_14b, st8_handling, st9_handling, st10_handling, st11_handling):
    global cycle_clock, prev_cycle_clock
    for pos in position:
        if pos == '3':
            if robot_2.process_complete:
                position[pos].process_complete = True
                robot_2.process_complete = False
        elif pos == '4':
            if robot_3.process_complete:
                position[pos].process_complete = True
                robot_3.process_complete = False
        elif pos == '10':
            if st8_handling.process_complete:
                position[pos].process_complete = True
                st8_handling.process_complete = False
        elif pos == '11':
            if st9_handling.process_complete:
                position[pos].process_complete = True
                st9_handling.process_complete = False
        elif pos == '12':
            if st10_handling.process_complete:
                position[pos].process_complete = True
                st10_handling.process_complete = False
        elif pos == '13':
            if st11_handling.process_complete:
                position[pos].process_complete = True
                st11_handling.process_complete = False
        elif pos == '17':
            if robot_14a.process_complete and robot_14b.process_complete:
                position[pos].process_complete = True
                robot_14a.process_complete, robot_14b.process_complete = False, False
        elif position[pos].time_in_station > position[pos].cycle_time and not position[pos].process_complete:
            position[pos].process_complete = True
            if pos == '21':
                prev_cycle_clock = cycle_clock
                cycle_clock = time
        next_pos = int(pos) + 1
        if next_pos > len(pallet_positions):
            next_pos = 1
        if position[pos].process_complete and position[str(next_pos)].time_without_pallet > pallet_clearing_time:
            position[pos].release(time)


run_simulation()
