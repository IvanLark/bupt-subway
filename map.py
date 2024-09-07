import json
from datetime import datetime, timedelta
import sys

STATIC_PATH = './static'

with open(f'{STATIC_PATH}/station.json', 'r', encoding='utf-8') as file:
    station_data = json.loads(file.read())

# time_data 层级结构：站点-->线路-->方向(0/1)-->星期-->小时-->分钟
with open(f'{STATIC_PATH}/time.json', 'r', encoding='utf-8') as file:
    time_data = json.loads(file.read())

with open(f'{STATIC_PATH}/point.json', 'r', encoding='utf-8') as file:
    point_data = json.loads(file.read())

station_list = list(station_data.keys())


# 上车cost
def get_rush_time(cur_time: datetime, rush_seconds: int, station: str, line: str, direction: str):
    day_dict = {
        '0': '工作日',
        '1': '工作日',
        '2': '工作日',
        '3': '工作日',
        '4': '工作日',
        '5': '双休日',
        '6': '双休日'
    }
    day_dict.keys()
    after_time = cur_time + timedelta(seconds=rush_seconds) # 中途换乘站换乘耗时，这里有可能变成第二天
    day_name = day_dict[str(after_time.weekday())] # 今天是工作日还是双休日
    hour_data = time_data[station][line][direction][day_name] # 列车小时分钟到站数据

    # 寻找能够赶上的列车到站时间
    def find_arrive_time():
        for hour_item in hour_data:
            # 如果这个小时有列车
            if int(hour_item) == after_time.hour:
                # 遍历每一个列车直到找到能上车的
                for minute_item in hour_data[hour_item]:  # TODO 可以用二分查找优化
                    if minute_item + 1 >= after_time.minute:  # 假设车停留一分钟
                        return hour_item, minute_item
            # 当前小时没有车了，到下一个小时
            if int(hour_item) > after_time.hour:
                return hour_item, hour_data[hour_item][0]

        # 考虑当前是否为23点然后看看0点有没有车
        if after_time.hour == 23 and '0' in hour_data:
            return '24', hour_data['0'][0]

        return None, None

    hour, minute = find_arrive_time()
    # 今天没有班车了
    if hour is None and minute is None:
        return None

    # 计算发车时间和当前时间的差值

    # 先化成整数
    hour = int(hour)
    minute = int(round(minute))
    # 然后考虑进位
    extra_hour = 0
    extra_minute = 0
    if hour >= 24:
        extra_hour = hour - 23
        hour = 23
    if minute >= 60:
        extra_minute = minute - 59
        minute = 59

    # 列车到站时间
    arrive_time = after_time.replace(hour=hour, minute=minute) + timedelta(hours=extra_hour, minutes=extra_minute)

    # 发车时间，真正的开车时间要加 1 分钟
    go_time = arrive_time + timedelta(minutes=1)

    # 返回秒数差值
    delta_time = (go_time - cur_time).total_seconds()

    # 绝对不能是负数，负数说明出bug了
    if delta_time < 0:
        print(
            f'after_hour: {after_time.hour}, after_minute: {after_time.minute}, 选中 hour: {hour}, minute: {minute}, go_time: {go_time}')
        return None

    # 如果说大于3个小时，那么就是第二天了，也是今天没车了
    elif delta_time > (60 * 60 * 3):
        return None

    return (go_time - cur_time).total_seconds()


class Strategy:
    BEST_TIMES = '最短时间'
    SHORTEST_DISTANCE = '最短距离'
    MINIMAL_TRANSFERS = '最少换乘'


def dijkstra_solve(cur_time: datetime, station_from: str, station_to: str, strategy):

    class Status:
        FINISHED = 1
        NOT_FINISHED = 0

    # 记录过程状态
    station_dict = {station: {
        'station': station,  # station名字
        'flag': Status.NOT_FINISHED,  # 是否已经找到最短路径
        'cost': sys.maxsize,  # 从起点到当前点最小花销
        'time': datetime.now() + timedelta(days=365),  # 到达时的时间
        'transfer': sys.maxsize,  # 到达所需换乘次数
        'distance': sys.maxsize, # 到达所需距离
        'pre': {  # 上一步信息
            'line': None,
            'direction': None,
        },
        'path': [] # 路径
    } for station in station_list}
    # 设置起点状态
    station_dict[station_from]['cost'] = 0
    station_dict[station_from]['time'] = cur_time
    station_dict[station_from]['transfer'] = 0
    station_dict[station_from]['distance'] = 0

    while True:
        cur_station = {
            'station': '',  # station名字
            'flag': Status.NOT_FINISHED,  # 是否已经找到最短路径
            'cost': sys.maxsize,  # 从起点到当前点最小花销
            'time': datetime.now() + timedelta(days=365),  # 到达时的时间
            'transfer': sys.maxsize,  # 到达所需换乘次数
            'distance': sys.maxsize, # 到达所需距离
            'pre': {  # 上一步信息
                'line': None,
                'direction': None,
            },
            'path': [] # 路径
        }
        # 找到cost最小的并且不是已完成的station
        for station_name in station_dict:
            station = station_dict[station_name]
            if station['flag'] == Status.NOT_FINISHED and station['cost'] < cur_station['cost']:
                cur_station = station

        # 没法找到cost最小的station，说明要么程序出错要么没车了
        if cur_station['station'] == '':
            # print([{'station': station, 'cost': '最大' if station_dict[station]['cost'] > 100000 else station_dict[station]['cost'], 'flag': station_dict[station]['flag']} for station in station_dict])
            return None

        # 标记找到最小的路径
        station_dict[cur_station['station']]['flag'] = Status.FINISHED

        # 当终点站已完成则返回
        if cur_station['station'] == station_to:
            return station_dict[cur_station['station']]['path']

        # 遍历这个station相邻的节点
        for link in station_data[cur_station['station']]['edge']:
            link_station_name = link['station']
            # 已完成则跳过
            if station_dict[link_station_name]['flag'] == Status.FINISHED:
                continue
            # 提取数据
            line = link['line']
            direction = link['directions']

            # 距离花销
            distance = link['distance']
            distance_cost = distance + cur_station['distance']

            # 时间花销和换乘花销
            ride_time = link['time']  # 乘车时间，单位：秒
            if line == cur_station['pre']['line'] and direction == cur_station['pre']['direction']:
                transfer = 0
                rush_time = 60 # 虽然不换乘但是要停车等60秒
            else:
                transfer = 1
                if cur_station['station'] == station_from:
                    rush_seconds = 0
                else:
                    rush_seconds = 60 * 3  # 假设花三分钟赶路
                # 赶路+等车时间，单位：秒
                rush_time = get_rush_time(
                    cur_time=cur_station['time'], rush_seconds=rush_seconds,
                    station=cur_station['station'], line=line, direction=str(direction)
                )
                if rush_time is None:
                    continue
            after_time = cur_station['time'] + timedelta(seconds=ride_time + rush_time)
            time_cost = (after_time - cur_time).total_seconds()
            transfer_cost = cur_station['transfer'] + transfer

            # 确定边的权重
            if strategy == Strategy.BEST_TIMES:
                cost = time_cost
            elif strategy == Strategy.SHORTEST_DISTANCE:
                cost = distance_cost
            elif strategy == Strategy.MINIMAL_TRANSFERS:
                cost = transfer_cost
            else:
                print('策略错误')
                return None

            # 如果当前花销更少，那么更新数据
            if cost < station_dict[link_station_name]['cost']:
                station_dict[link_station_name]['cost'] = cost
                station_dict[link_station_name]['time'] = after_time
                station_dict[link_station_name]['transfer'] = transfer_cost
                station_dict[link_station_name]['distance'] = distance_cost
                station_dict[link_station_name]['pre']['line'] = line
                station_dict[link_station_name]['pre']['direction'] = direction
                station_dict[link_station_name]['path'] = cur_station['path'] + [{
                    'source': cur_station['station'], 'target': link_station_name, 'line': line, 'direction': direction,
                    'rush_cost': rush_time, 'ride_cost': ride_time, 'time': after_time, 'time_cost': time_cost,
                    'distance': distance, 'distance_cost': distance_cost,
                    'transfer': transfer, 'transfer_cost': transfer_cost
                }]
