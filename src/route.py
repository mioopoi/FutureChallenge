# coding=utf-8

import pandas as pd
from collections import namedtuple
from container import PriorityQueue
import math
import time

# 只考虑影响无人飞行器坠毁的两个天气因素：风速和降雨量。
# 当风速值≥15时，或者降雨量≥4时，无人机坠毁。
MAX_SPEED = 13.65  # wind threshould
MAX_RAIN = 3.70    # rainfall threshould

Node = namedtuple("Node", ['xid', 'yid', 'hour', 'step'])


def load_weather(filename):
    df = pd.read_csv(filename)
    print("load wind data...")
    start = time.clock()
    weather = dict()
    k = 0
    for index, row in df.iterrows():
        k += 1
        if math.fmod(k, 100000) == 0:
            print("load {} data".format(k))
        xid = row['xid']
        yid = row['yid']
        hour = row['hour']
        w = row['wind']
        r = row['rainfall']
        weather[(xid, yid, hour)] = (w, r)
    elapsed = time.clock() - start
    print("total init time: {} seconds\n".format(elapsed))  # about 188s
    return weather


class Solver:
    def __init__(self, weather, date_id):
        self.date_id = date_id  # type: int
        self.weather = weather
        self.start_xid, self.start_yid = 142, 328
        self.target_xid, self.target_yid = 142, 328
        self.start_node = Node(self.start_xid, self.start_yid, 3, 0)
        self.real_end_node = None

        targets = dict()
        targets[1] = (84, 203)
        targets[2] = (199, 371)
        targets[3] = (140, 234)
        targets[4] = (236, 241)
        targets[5] = (315, 281)
        targets[6] = (358, 207)
        targets[7] = (363, 237)
        targets[8] = (423, 266)
        targets[9] = (125, 375)
        targets[10] = (189, 274)
        self.targets = targets

    def run(self):
        targets = self.targets
        # 每天3点钟10架推进式无人运输飞行器将开始从伦敦海德公园飞往英国其他10个目的地城市，
        # 限定任意两架无人飞行器起飞时间必须间隔大于等于10分钟，
        # 且最大飞行时长为18个小时 [03:00-21:00)，
        # 最晚21:00及之前必须到达目的地城市。
        for target_id in targets:
        # for target_id in range(1, 11):
            print("\n\n===== 开始规划到达目标城市{}的路径 =====".format(target_id))
            start_hour, start_step = self.start_node.hour, self.start_node.step
            # 设置起飞时刻
            # 任意两架无人飞行器起飞时间必须间隔大于等于10分钟!
            if target_id != 1:
                start_step += 5
                if start_step >= 30:
                    start_hour += 1
                    start_step = start_step % 30
                self.start_node = Node(self.start_xid, self.start_yid, start_hour, start_step)
            # 检查起飞时刻的天气状况，如果无法起飞，就延续到下一个小时，直到可以起飞为止
            ret = self._check_start_pos()
            while ret != 0:
                if ret == 1:
                    return
                print("起飞时刻延后一小时")
                start_hour += 1
                start_step = 0
                self.start_node = Node(self.start_xid, self.start_yid, start_hour, start_step)
                ret = self._check_start_pos()
            print("允许起飞, "),
            print("第{}架无人机的起飞时刻为{}".format(target_id, (self.start_node.hour, self.start_node.step * 2)))
            tmp = (self.start_node.xid, self.start_node.yid, self.start_node.hour)
            print("起飞时的天气状况为：风速{}，降雨量{}".format(self.weather[tmp][0], self.weather[tmp][1]))

            self.target_xid, self.target_yid = targets[target_id][0], targets[target_id][1]

            # 估计飞行时长
            # eva_steps = (abs(self.start_node.xid - self.target_xid) + abs(self.start_node.yid - self.target_yid)) * 1.2
            # eva_steps = int(eva_steps)
            # eva_hour_lower = 3 + eva_steps / 30

            # 规划飞行线路
            # self._search_one_target(target_id, eva_hour_lower)
            self._search_one_target_0(target_id)

    def _check_start_pos(self):
        tmp = (self.start_node.xid, self.start_node.yid, self.start_node.hour)
        if tmp not in self.weather:
            print("起飞时刻超限, 航班取消。")
            return 1
        if self.weather[tmp][0] >= MAX_SPEED or self.weather[tmp][1] >= MAX_RAIN:
            print("起飞时刻天气不允许")
            return 2
        return 0

    def _search_one_target_0(self, target_id):
        # 估计飞行时长
        eva_steps = (abs(self.start_node.xid - self.target_xid) + abs(self.start_node.yid - self.target_yid)) * 2.0
        eva_steps = int(eva_steps)
        eva_hour = min(3 + eva_steps / 30, 15)
        # eva_hour = 15
        eva_step = 0
        self.end_node = Node(self.target_xid, self.target_yid, eva_hour, eva_step)
        self.real_end_node = None

        print("Search the route of city {}...".format(target_id))
        path = self.search_path()
        # path = self.search_path_greedy_best_first()
        if len(path) == 0:
            print("Search failed, no path.")
            return
        self.check_path(path)
        print("We have found a path to City {}!".format(target_id))
        print("The length of the path is {}".format(len(path)))
        print("到达目的地的时刻为{}:{}".format(self.real_end_node.hour, self.real_end_node.step * 2))
        with open('../results_tmp/%d_%d.csv' % (self.date_id, target_id), 'w') as f:
            for node in path:
                f.write("%d,%d,%d,%d\n" % (node.xid, node.yid, node.hour, node.step * 2))
        return

    def _search_one_target(self, target_id, eva_hour_lower):
        for eva_hour in range(eva_hour_lower, 21):
            tmp = (self.target_xid, self.target_yid, eva_hour)
            if self.weather[tmp] >= 15.0 or self.weather[tmp] >= 4.0:
                print("Eva hour infeasible.")
                continue
            for eva_step in range(0, 30):
                print("估计到达时刻: %d:%d" % (eva_hour, eva_step * 2))
                self.end_node = Node(self.target_xid, self.target_yid, eva_hour, eva_step)
                self.real_end_node = None
                print("Search the route of city %d..." % target_id)
                path = self.search_path()
                if len(path) == 0:
                    continue
                # We have found a path!
                print("发现到达城市{}的路径!".format(target_id))
                with open('./results_tmp/%d_%d.csv' % (self.date_id, target_id), 'w') as f:
                    for node in path:
                        f.write("%d,%d,%d,%d\n" % (node.xid, node.yid, node.hour, node.step * 2))
                return

    def search_path(self):
        frontier = PriorityQueue()
        frontier.put(self.start_node, 0)
        came_from = {}
        cost_so_far = {}
        visited_site = {}
        came_from[self.start_node] = None
        cost_so_far[self.start_node] = 0

        self.real_end_node = None

        s_t = time.clock()

        while not frontier.empty():
            if time.clock() - s_t > 60:
                print("search path time out.")
                return []

            current = frontier.get()  # type: Node
            cur_site = (current.xid, current.yid)

            if current.xid == self.target_xid and current.yid == self.target_yid:
                self.real_end_node = current
                break

            # inspect five (include itself) neighbors
            neighbors = self._get_neighbors(current)
            for nb in neighbors:
                new_cost = cost_so_far[current] + self._get_cost(current, nb)
                next_site = (nb.xid, nb.yid)
                if nb not in cost_so_far or new_cost < cost_so_far[nb]:
                    if next_site == cur_site and next_site in visited_site:
                        cost_so_far[nb] = new_cost + 2
                    else:
                        cost_so_far[nb] = new_cost
                    visited_site[next_site] = (nb.hour, nb.step)
                    priority = cost_so_far[nb] + self.heuristic(nb, self.end_node)
                    frontier.put(nb, priority)
                    came_from[nb] = current

        if self.real_end_node is None:
            return []

        path = [self.real_end_node]
        now = self.real_end_node
        while came_from[now] is not None:
            now = came_from[now]
            path.append(now)
        path.reverse()

        return path

    def search_path_greedy_best_first(self):
        frontier = PriorityQueue()
        frontier.put(self.start_node, 0)
        came_from = dict()
        came_from[self.start_node] = None

        self.real_end_node = None

        s_t = time.clock()

        while not frontier.empty():
            if time.clock() - s_t > 60:
                print("search path time out.")
                return []

            current = frontier.get()  # type: Node

            if current.xid == self.target_xid and current.yid == self.target_yid:
                self.real_end_node = current
                break

            # inspect five (include itself) neighbors
            neighbors = self._get_neighbors(current)
            for nb in neighbors:
                if nb not in came_from:
                    priority = self.heuristic(nb, self.end_node)
                    frontier.put(nb, priority)
                    came_from[nb] = current

        if self.real_end_node is None:
            return []

        path = [self.real_end_node]
        now = self.real_end_node
        while came_from[now] is not None:
            now = came_from[now]
            path.append(now)
        path.reverse()

        return path

    def _get_cost(self, node1, node2):
        """
        :type node1: Node
        :type node2: Node
        :return:
        """
        if node1.xid == node2.xid and node1.yid == node2.yid:
            return 0
        else:
            return 1

    def _get_neighbors(self, node):
        """
        :type node: Node
        :return a list contains all the neighbors of node
        """
        neighbors = []
        hour, step = node.hour, node.step + 1
        if step == 30:
            hour += 1
            step = 0
        if hour <= 20:
            n1 = Node(node.xid + 1, node.yid, hour, step)
            n2 = Node(node.xid - 1, node.yid, hour, step)
            n3 = Node(node.xid, node.yid + 1, hour, step)
            n4 = Node(node.xid, node.yid - 1, hour, step)
            n5 = Node(node.xid, node.yid, hour, step)
            ns = [n1, n2, n3, n4, n5]
            # check the weather of each neighbor
            for nb in ns:
                tmp = (nb.xid, nb.yid, nb.hour)
                if tmp not in self.weather:
                    continue
                (wind, rain) = self.weather[tmp]
                if wind <= MAX_SPEED and rain <= MAX_RAIN:
                    neighbors.append(nb)
                elif tmp[0] == self.target_xid and tmp[1] == self.target_yid and wind < 15.0 and rain < 4.0:
                    neighbors.append(nb)
        return neighbors

    def heuristic(self, a, b):
        """
        :type a: Node
        :type b: Node
        """
        h1, h2 = a.hour, b.hour
        s1, s2 = a.step, b.step
        if h1 > h2:
            h1, h2 = b.hour, a.hour
            s1, s2 = b.step, a.step
        gap = 0
        if h1 == h2:
            gap = abs(s2 - s1)
        else:
            gap = (30 - s1) + (h2 - h1 - 1) * 30 + s2
        return abs(a.xid - b.xid) + abs(a.yid - b.yid) + abs(gap) * 0.5

        # return abs(a.xid - b.xid) + abs(a.yid - b.yid)

    def check_path(self, path):
        """
        :type path: list[Node]
        """
        # check start and end
        if path[0] != self.start_node:
            print("path start invalid")
            return False
        if path[-1].xid != self.target_xid or path[-1].yid != self.target_yid:
            print("path end invalid")
            return False

        # check weather feasibility
        for node in path:
            tmp = (node.xid, node.yid, node.hour)
            (wind, rain) = self.weather[tmp]
            print(wind, rain)
            if wind > MAX_SPEED or rain > MAX_RAIN:
                print("path passes through dangerous node")
        print()

        # check consistence feasibility
        for i in range(1, len(path)):
            if abs(path[i].xid - path[i - 1].xid) + abs(path[i].yid - path[i - 1].yid) > 1:
                print("path node position not consistent")
                return False
            if path[i].hour < path[i - 1].hour:
                print("path node time not consistent")
                return False
            elif path[i].hour == path[i - 1].hour:
                if path[i].step < path[i - 1].step or path[i].step > path[i - 1].step + 1:
                    print("path node time not consistent")
                    return False
            else:
                if path[i].hour > path[i - 1].hour + 1:
                    print("path node time not consistent")
                    return False
                if path[i].step != 0 or path[i - 1].step != 29:
                    print("path node time not consistent")
                    return False

        print("Successfully pass the feasibility check.\n")
        return True


if __name__ == '__main__':
    for day in range(6, 11):
        print("**********Solve for date {}**********".format(day))
        weather_today = load_weather('../merge_data/MergeData%d.csv' % day)
        solver = Solver(weather_today, day)
        solver.run()
