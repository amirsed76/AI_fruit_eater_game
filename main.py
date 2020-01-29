import socket
import struct
import random
from enum import Enum
import collections
from pip._vendor.distlib.metadata import _best_version


class Directions(Enum):
    UP, DOWN, LEFT, RIGHT = 'UP', 'DOWN', 'LEFT', 'RIGHT'


class AI:

    def __init__(self, bot_id, bot_count, board_size, max_turn):
        self.bot_id, self.__bot_count, self.__board_size = bot_id, bot_count, board_size
        self.score_board = []
        self.all_fruits = ['A', 'B', 'C', 'O', 'W']
        self.board = []
        self.fruits = ""
        self.cell_value = dict()
        self.avoids = []
        self.current_loc = self.my_player_location()
        self.accessibility_list = []
        self.constraint1_cost = 50
        self.constraint2_cost = 40
        self.constraint3_cost = 30
        self.score_board2 = []
        self.point = 0
        self.constraint1 = False
        self.constraint2 = True
        self.constraint3 = True
        self.scope = self.__board_size * 2
        self.total_turn = max_turn
        self.remainder_turn = self.total_turn + 1
        self.hope_constraint1 = True
        self.hope_constraint2 = True
        self.hope_constraint3 = True
        self.bot_count = bot_count
        self.ai_opps = []

    def do_turn(self):
        try:
            self.fill_scoreboard()
            self.current_loc = self.my_player_location()
            goal = self.find_best_cell()
            print("GOAL", goal, " ", self.board[goal[0]][goal[1]])
            route = self.modified_bfs(grid=self.board, start=self.current_loc, goal=goal, width=len(self.board), avoids=[])
            print("bfs")
            nav = navigation(route)

        except Exception as e:
            nav = Directions.UP
        return nav

    def set_scope(self):
        self.scope = min([self.scope, self.remainder_turn])
        if self.scope <= 0:
            self.scope = 1

    def hope_status(self):
        self.hope_constraint2 = True
        self.hope_constraint3 = True
        if self.bot_count > 1:
            try:
                ai_max_fruits = max(self.ai_opps, key=lambda item: len(item.fruits))
                ai_max_fruits_count = len(ai_max_fruits.fruits)
            except Exception as e:
                print("EX", e)
                ai_max_fruits_count = 0

            all_fruits_count_in_board = self.board.count("B") + self.board.count("W") + self.board.count("C") + self.board.count(
                "A") + self.board.count("O")

            if self.remainder_turn < self.total_turn / 2:
                if len(self.fruits) < ai_max_fruits_count and ai_max_fruits_count > (
                        self.total_turn - self.remainder_turn) / 4:
                    if not self.constraint2:
                        self.hope_constraint2 = False
                    if not self.constraint3:
                        self.hope_constraint3 = False

                if self.fruits.count("B") * 2 - self.fruits.count("O") > (self.remainder_turn / 6) and (
                        all_fruits_count_in_board / self.scope) > 0.5:
                    if not self.constraint2:
                        self.hope_constraint2 = False

                if self.fruits.count("W") + self.fruits.count("C") - self.fruits.count("A") > (
                        self.remainder_turn / 6) and (all_fruits_count_in_board / self.scope) > 0.5:
                    if not self.constraint3:
                        self.hope_constraint3 = False

            divisor = 4
            if self.__board_size < 8:
                divisor = 3
            elif 8 <= self.__board_size < 10:
                divisor = 4

            elif 10 <= self.__board_size < 12:
                divisor = 5
            elif 12 <= self.__board_size:
                divisor = 6

            if self.remainder_turn < (self.total_turn / divisor):
                if not self.constraint2:
                    self.hope_constraint2 = False
                if not self.constraint3:
                    self.hope_constraint3 = False

    def point_status(self):
        """ calculate current point"""
        self.point = 0
        if not self.constraint1:
            self.point -= self.constraint1_cost

        if not self.constraint2:
            self.point -= self.constraint2_cost

        if not self.constraint3:
            self.point -= self.constraint3_cost

        self.point += self.fruits.count("B") * 5
        self.point += self.fruits.count("A") * 1
        self.point += self.fruits.count("C") * 2
        self.point += self.fruits.count("O") * 1
        self.point += self.fruits.count("W") * 3

    def constraint_status(self):
        """calculate current constraints"""
        self.constraint1 = True
        self.constraint2 = False
        self.constraint3 = False
        for fruit in self.all_fruits:
            if fruit not in self.fruits:
                self.constraint1 = False
                break
        if self.fruits.count("O") >= 2 * self.fruits.count("B"):
            self.constraint2 = True
        else:
            self.constraint2 = False

        if self.fruits.count("A") >= (self.fruits.count("C") + self.fruits.count("W")):
            self.constraint3 = True
        else:
            self.constraint3 = False

    def constraint_status2(self, will_fruits):
        """calculate current constraints"""
        # print("WILL FRUIT", will_fruits)
        constraint1 = True
        constraint2 = False
        constraint3 = False
        for fruit in self.all_fruits:
            if fruit not in will_fruits:
                constraint1 = False
                break
        if will_fruits.count("O") >= 2 * will_fruits.count("B"):
            constraint2 = True
        else:
            constraint2 = False

        if will_fruits.count("A") >= (will_fruits.count("C") + will_fruits.count("W")):
            constraint3 = True
        else:
            constraint3 = False

        return (constraint1, constraint2, constraint3)

    def score_board_init(self):
        self.score_board = []
        for index in range(board_size):
            self.score_board.append([])
            for index2 in range(board_size):
                self.score_board[index].append(0)

    def make_avoid_cells(self):
        self.avoids = []
        try:
            # print("SCORE BOARD",self.score_board)
            for index1, row in enumerate(self.score_board):
                for index2, point in enumerate(row):
                    if point < 0:
                        self.avoids.append((index1, index2))
        except:
            pass

    def fill_scoreboard(self):
        """allocate point foreach cell in grid
            fill score board
        """
        self.score_board_init()
        self.cell_evaluate()
        for index, row in enumerate(self.board):
            for index2, char in enumerate(row):
                try:
                    self.score_board[index][index2] = self.cell_value[char] - self.manhatan(end=(index, index2)) * (
                                200 / self.__board_size)
                except Exception as e:
                    self.score_board[index][index2] = 0

                if self.manhatan((index, index2)) > self.scope:
                    self.score_board[index][index2] = -10000

                if self.accessibility_list[index][index2] == False:
                    self.score_board[index][index2] = -10000

                nearest_opp_manhatan = self.nearest_opponent_manhatan((index, index2))
                my_manhatan = self.manhatan(end=(index, index2))
                if nearest_opp_manhatan < my_manhatan + 2:
                    self.score_board[index][index2] += (nearest_opp_manhatan - my_manhatan) * 20

                if char == ".":
                    self.score_board[index][index2] = self.cell_value[char] - self.manhatan(
                        first=(self.__board_size / 2, self.__board_size / 2), end=(index, index2))

                if self.manhatan(end=(index, index2)) == 1:
                    if char == "O" or char == "A":
                        self.score_board[index][index2] = 1000000

    def nearest_opponent_manhatan(self, goal):
        try:
            opp_list = ["0", "1", "2", "3"]
            manhatan_list = []
            opp_list.remove(str(self.bot_id))
            for index1, row in enumerate(self.board):
                for index2, char in enumerate(row):
                    if char in opp_list:
                        roate = bfs(grid=self.board, start=(index1, index2), goal=goal, width=self.__board_size,
                                    avoids=[])
                        if roate is not None:
                            manhatan_list.append(len(roate))

            if len(manhatan_list) != 0:
                return min(manhatan_list)
            else:
                return 0
        except Exception as e:
            print(e, 1)
            return 0

    def cell_evaluate(self):
        """allocate point foreach character of grid """

        self.cell_value["A"] = 500 + self.__board_size * 2
        self.cell_value["B"] = 100 + self.__board_size * 2
        self.cell_value["C"] = 400 + self.__board_size * 2
        self.cell_value["O"] = 500 + self.__board_size * 2
        self.cell_value["W"] = 300 + self.__board_size * 2
        self.cell_value["0"] = -10000
        self.cell_value["1"] = -10000
        self.cell_value["2"] = -10000
        self.cell_value["3"] = -10000
        self.cell_value["*"] = -100000
        self.cell_value["."] = self.__board_size * 2
        self.cell_value["I"] = 0
        self.cell_value[str(self.bot_id)] = self.__board_size * 2
        count = dict()
        for key in self.cell_value.keys():
            count[key] = self.fruits.count(key)
            if count[key] == 0 and key in ["A", "B", "C", "O", "W"]:
                if key == "A":
                    self.cell_value[key] += 80000
                if key == "O":
                    self.cell_value[key] += 80000

                amount = 200
                if 8 < self.__board_size <= 10:
                    amount = 300
                if self.__board_size <= 8:
                    amount = 400

                if key == "W":
                    self.cell_value[key] += amount + (self.__board_size * 2) + (
                                self.total_turn / self.remainder_turn) * 5
                if key == "C":
                    self.cell_value[key] += amount + (self.__board_size * 2) + (
                                self.total_turn / self.remainder_turn) * 5
                if key == "B":
                    self.cell_value[key] += amount - 100 + (self.__board_size * 2) + (
                                self.total_turn / self.remainder_turn) * 5

            if key in ["A", "B", "C", "O", "W"]:
                will_foods = self.fruits + key
                c1, c2, c3 = self.constraint_status2(will_foods)
                if c1 and c2 and c3:
                    self.cell_value[key] = 10000000

        if count["B"] != 0:
            if int(count["O"] / 2) <= count["B"] and self.hope_constraint2:
                self.cell_value["B"] -= ((self.constraint2_cost * 100 + 20) + self.__board_size * 2)
        if count["A"] <= count["C"] + count["W"] and self.hope_constraint3:
            if count["C"] != 0:
                self.cell_value["C"] -= ((self.constraint3_cost * 100 + 20) + self.__board_size * 2)
            if count["W"] != 0:
                self.cell_value["W"] -= ((self.constraint3_cost * 100 + 20) + self.__board_size * 2)

        if not self.hope_constraint2:
            self.cell_value["B"] += 500
        if not self.hope_constraint3:
            self.cell_value["W"] += 300
            self.cell_value["W"] += 200

        self.cell_value["0"] = -10000
        self.cell_value["1"] = -10000
        self.cell_value["2"] = -10000
        self.cell_value["3"] = -10000
        self.cell_value["*"] = -100000
        self.cell_value[str(self.bot_id)] = self.__board_size * 2


        try:
            fruit = self.fruits[-1]
            self.cell_value[fruit] += 100
        except:
            pass

        try:
            if self.fruits[-1]==self.fruits[-2]:
                fruit = self.fruits[-1]
                self.cell_value[fruit] += 200
        except:
            pass

    def print_score_board(self):
        """print score board"""
        for row in self.score_board:
            print(row)

    def print_grid(self):
        """print board"""
        for row in self.board:
            print(row)

    def my_player_location(self):
        """find my player location"""
        for index, row in enumerate(self.board):
            index2 = str(row).find(str(self.bot_id))
            if index2 > -1:
                # print("MY location=",(index,index2))
                return index, index2

    def manhatan(self, end, first=None):
        """calculate manhatan"""
        if first is None:
            current_loc = self.my_player_location()
        else:
            current_loc = first
        try:
            return abs(int(end[0]) - int(current_loc[0])) + abs(int(end[1]) - int(current_loc[1]))
        except Exception as e:
            # print("EXPPPPPPP", e)
            return 0

    def find_best_cell(self):
        """find best cell"""
        maximum = -1
        index1 = -1
        index2 = -1
        min_manhatan = 10000

        try:
            x, y = self.my_player_location()
            for i, row in enumerate(self.score_board):
                for j, point in enumerate(row):
                    if point >= maximum:
                        index1 = i
                        index2 = j
                        maximum = point
                        if point == maximum:
                            if min_manhatan > self.manhatan(first=(x, y), end=(i, j)):
                                index1 = i
                                index2 = j
                                maximum = point
                                min_manhatan = self.manhatan(first=(x, y), end=(i, j))

                        else:
                            index1 = i
                            index2 = j
                            maximum = point
                            min_manhatan = self.manhatan(first=(x, y), end=(i, j))

        except Exception as e:
            # print("EXXXXX", e)
            return (1, 1)

        return (index1, index2)

    def accessibility(self):
        """allocate True and False for each cell based accessibility"""
        accessibility = []
        print(self.board)
        print(self.__board_size)
        for index1 in range(self.__board_size):
            accessibility.append([])
            for index2 in range(self.__board_size):
                print("cuurent", self.my_player_location())
                if bfs(self.board, self.my_player_location(), (index1, index2), self.__board_size, []) is not None:
                    accessibility[index1].append(True)
                else:
                    accessibility[index1].append(False)
        self.accessibility_list = accessibility.copy()

    def modified_bfs(self, grid, start, goal, width, avoids, timeout=None, timeout2=None):
        """bfs"""
        if timeout is None:
            timeout = self.__board_size * (100)
            # timeout = self.__board_size*100
        if timeout2 is None:
            timeout2 = 8
        pathesQueue = collections.deque([[start]])
        index = 0
        flag = False
        pathes = []
        while pathesQueue and index < timeout:
            if flag:
                index += 1
            path = pathesQueue.popleft()
            x, y = path[-1]
            if (x, y) == goal:
                # print("_______________________________ find goal")
                if len(pathes) > 0:
                    if len(path) <= len(pathes[0]):
                        pathes.append(path)
                else:
                    flag = True
                    pathes.append(path)
            for x2, y2 in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                try:
                    if 0 <= x2 < width and 0 <= y2 < width and grid[x2][y2] != "*" and (x2, y2) not in path and (
                            x2, y2) not in avoids:
                        pathesQueue.append(path + [(x2, y2)])
                except:
                    pass
                    # if not flag:
                    # seen.add((x2, y2))
        if len(pathes) != 0:
            min_len = len(pathes[0])
            best_path = max(pathes, key=lambda item: self.path_point(item, min_len))
            if self.path_point(best_path, min_len) >= 0:
                return best_path

            else:
                if timeout2 == 0:
                    x,y = self.current_loc
                    x_y_list=[]
                    for x2, y2 in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        try:
                            if 0 <= x2 < width and 0 <= y2 < width and grid[x2][y2] != "*" and (
                            x2, y2) not in path and (x2, y2) not in avoids:
                                x_y_list.append((x2,y2))
                        except:
                            pass
                    try:
                        loc2 = max(x_y_list , key= lambda item:self.score_board[item[0]][item[1]])
                    except Exception as e :
                        # print("ERTYU",e)
                        return best_path

                    best_path=[self.current_loc  ,loc2 ]
                    return best_path
                x, y = goal
                self.score_board[x][y] = -100000
                timeout2 -= 1
                goal = self.find_best_cell()
                print("BFSSSSS")
                return self.modified_bfs(grid, start, goal, width, avoids, timeout, timeout2)

        return None

    def path_point(self, path2, min_len):
        list_point=[]
        for index in range(len(path2)):
            will_eat = ""
            path=path2[:index+1]
            for (x, y) in path:
                if self.board[x][y] in ["A", "B", "C", "O", "W"]:
                    will_eat += self.board[x][y]

            eated = self.fruits
            result_eat = will_eat + eated

            result_constraint1, result_constraint2, result_constraint3 = self.constraint_future(result_eat=result_eat)

            point = 0

            try:
                if len(path) > 1:
                    x, y = path[1]
                    bot_list=["0", "1", "2", "3"]
                    bot_list.remove(str(self.bot_id))
                    if self.board[x][y] in bot_list:
                        point -= 1000
            except:
                pass
            if not result_constraint1 and self.hope_constraint1:
                point -= (self.constraint1_cost * 10)

            if not result_constraint2 and self.constraint1 and self.hope_constraint2:
                point -= (self.constraint2_cost * 10)

            if not result_constraint3 and self.constraint1 and self.hope_constraint3:
                point -= (self.constraint3_cost * 10)

            try:
                will_eat2 = eated[-2:] + will_eat
            except:
                will_eat2 = will_eat
            sequential = 0
            last_fruit = "Y"
            if self.hope_constraint2 and self.hope_constraint3:
                for friut in will_eat2:
                    if self.bot_count > 1:
                        if friut == last_fruit:
                            sequential += 1
                        else:
                            sequential = 1
                        last_fruit = friut
                        if sequential == 3:
                            sequential = 0
                            last_fruit = "y"
                            point += 20
            try:
                if len(eated) > 2 and eated[-1] == eated[-2]:
                    if will_eat[0] == eated[-1]:
                        # point+=36
                        for ai2 in self.ai_opps:
                            if len(ai2.fruits) > 1:
                                current_point = ai2.point
                                last_fruit = ai2.fruits[-1]
                                ai2.fruits = ai2.fruits[:-1]
                                ai2.constraint_status()
                                ai2.point_status()
                                ai2.point_status()
                                point += (current_point - ai2.point) * 20
                                ai2.fruits += last_fruit
                                ai2.constraint_status()
                                ai2.point_status()

            except Exception as e:
                # print("EXEPTION", e)
                pass

            if not self.hope_constraint2:
                point += will_eat.count("B") * 50

            if not self.hope_constraint3:
                point += will_eat.count("W") * 30
                point += will_eat.count("C") * 20

            if self.hope_constraint2:
                point += (result_eat.count("O") - result_eat.count("B") * 2) * (self.constraint2_cost*10)
            if self.hope_constraint3:
                point += (result_eat.count("A") - (result_eat.count("C") + will_eat.count("W"))) * (
                            self.constraint3_cost*10 )
            point += result_eat.count("B") * 50
            point += result_eat.count("W") * 30
            point += result_eat.count("C") * 20
            point += result_eat.count("O") * 60
            point += result_eat.count("A") * 60

            if result_constraint1 and result_constraint2 and result_constraint3:
                print("FINISH HIM ")
                # if len(finish_path) == 0:
                #     finish_path=path
                point = 1000000000 - len(path)*100 - len(will_eat) - self.manhatan(end=path[-1])

            list_point.append((point - self.point * 10) - (len(path) - min_len) * (2 ** self.bot_count) + 30)
            # return (point - self.point * 10) - (len(path) - min_len) * (2 ** self.bot_count) + 30
        return max(list_point)
        # return point - self.point*10 - (len(path) - min_len)*(2**self.bot_count)-(will_eat.count(".")-min_len)

    def constraint_future(self, result_eat):
        result_constraint1 = True
        for fruit in self.all_fruits:
            if fruit not in result_eat:
                result_constraint1 = False
                break

        if result_eat.count("O") >= 2 * result_eat.count("B"):
            result_constraint2 = True
        else:
            result_constraint2 = False

        if result_eat.count("A") >= result_eat.count("C") + result_eat.count("W"):
            result_constraint3 = True
        else:
            result_constraint3 = False

        return (result_constraint1, result_constraint2, result_constraint3)


    def make_scoreboard2(self):
        for x, row in enumerate(self.score_board):
            self.score_board2.append([])
            for y, col in enumerate(row):
                list = []
                result = self.score_board[x][y] * 8
                for (x2, y2) in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                    if 0 <= x2 < self.__board_size and 0 <= y2 < self.__board_size and self.score_board[x2][y2] > 0:
                        list.append(self.score_board[x2][y2])
                result += sum(list)
                result /= (8 + len(list))
                if self.score_board[x][y] > 0:
                    self.score_board2[x].append(result)

                else:
                    self.score_board2[x].append(self.score_board[x][y])


def navigation(route):
    try:
        next_step = route[1]
        current_step = route[0]
        destination = (next_step[0] - current_step[0], next_step[1] - current_step[1])
        if destination == (0, 1):
            return Directions.RIGHT
        if destination == (0, -1):
            return Directions.LEFT
        if destination == (1, 0):
            return Directions.DOWN
        if destination == (-1, 0):
            return Directions.UP
    except:
        return Directions.UP


def read_utf(sock: socket.socket):
    length = struct.unpack('>H', s.recv(2))[0]
    return sock.recv(length).decode('utf-8')


def write_utf(sock: socket.socket, msg: str):
    sock.send(struct.pack('>H', len(msg)))
    sock.send(msg.encode('utf-8'))


def routing(source, destination):
    pass


def bfs(grid, start, goal, width, avoids):
    # print("grid", grid)
    # print("start", start)
    # print("goal", goal)
    # print("width", width)
    # print("avoids", avoids)
    queue = collections.deque([[start]])
    seen = set([start])
    while queue:
        path = queue.popleft()
        x, y = path[-1]
        if (x, y) == goal:
            return path
        near_cells = []
        for x2, y2 in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= x2 < width and 0 <= y2 < width and grid[x2][y2] != "*" and (x2, y2) not in seen and (
                    x2, y2) not in avoids:
                queue.append(path + [(x2, y2)])
                seen.add((x2, y2))


def list_to_str(list):
    string = ""
    for i in list:
        string += str(i)
    return string


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.43.147', 9898))
    init_data = read_utf(s)
    bot_id, bot_count, board_size, max_turn = map(int, init_data.split(','))
    ai = AI(bot_id, bot_count, board_size, max_turn)
    cycle = 0
    ai_list = []
    for id in range(bot_count):
        if id != bot_id:
            ai2 = AI(id, bot_count, board_size, max_turn)
            ai_list.append(ai2)
    while True:
        print("cycle_____________________________", cycle)
        board_str = read_utf(s)
        board = [board_str[i * board_size:(i + 1) * board_size] for i in range(board_size)]
        ai.board = board
        fruits = [read_utf(s) for _ in range(bot_count)]
        for f in fruits:
            if f[0] == str(bot_id):
                ai.fruits = f[1:]
        if cycle == 0:
            ai.accessibility()
            # print(ai.accessibility_list)
        # print("FRUITS", fruits)

        for ai2 in ai_list:
            ai2.fruits = fruits[ai2.bot_id]
            ai2.constraint_status()
            ai2.point_status()
            # print("ENEMY" , ai2.constraint1,ai2.constraint2,ai2.constraint3)
            ai.fruits = fruits[bot_id]
        for fruit in fruits:
            if str(ai.bot_id) in fruit:
                ai.fruits = fruit
        # print("FRUIT", ai.fruits)
        ai.constraint_status()
        ai.point_status()
        # print("points= ", ai.point)
        # print("Scope",ai.scope)
        ai.remainder_turn -= 1
        ai.set_scope()
        ai.hope_status()
        print("ID", bot_id)
        print("HOP", ai.hope_constraint1, ai.hope_constraint2, ai.hope_constraint3)
        ai.ai_opps = ai_list
        print("CONSTRAINT", ai.constraint1, " ", ai.constraint2, " ", ai.constraint3)

        write_utf(s, ai.do_turn().value)

        cycle += 1
