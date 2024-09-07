import streamlit as st
import re
from map import Strategy, dijkstra_solve, station_data, station_list
from datetime import datetime, timedelta

st.set_page_config(page_title='北京地铁线路查询')

st.title("🚇北京地铁线路查询")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "欢迎你！我是北京地铁路线查询bot，你可以问我从哪个站到哪个站要怎么走？可以要求最短时间或最少换乘次数或最短距离的路线。提问中要出现\"从XX\"和\"到XX\"的字样。\n\n例子：从沙河到西土城怎么走？要求有最短时间路线和最少换乘路线。\n\n注：由于大多数站点的列车到达时间均为粗略估算，难免与真实时间有一定偏差。"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    def reply(response_message: str):
        st.session_state.messages.append({"role": "assistant", "content": response_message})
        st.chat_message("assistant").markdown(response_message)

    def generate_path_content(station_from_name, station_to_name, strategy_name, edge_list):
        content = f'### 从{station_from}到{station_to}的{strategy}路线:\n\n'

        cur_line = '' # 当前路线
        cur_start = '' # 当前路线起始站
        cur_end = '' # 当前路线终点站
        cur_rush_time = 0 # 当前路线上车时间
        cur_cost_time = 0 # 当前路线总乘车时间

        content += '#### 乘坐地铁路线\n\n'
        for index in range(len(path)):
            edge = path[index]

            cur_cost_time += edge['ride_cost'] + edge['rush_cost'] # 每次加一次乘车时间

            # 如果换乘那么要输出上一段，并且记录下一段
            if edge['line'] != cur_line:
                cur_end = edge['source']  # 上一段的终点站
                # 如果不是起始的edge那么输出上一段
                if cur_line != '' and cur_start != '':
                    content += f'在**{cur_start}**站换乘或等车**{round(cur_rush_time / 60)}**分钟，乘坐**{cur_line[:cur_line.find('(')]}**，从**{cur_start}**站坐到**{cur_end}**站，总共花费**{round(cur_cost_time / 60)}**分钟\n\n'
                # 更新下一段的数据
                cur_start = edge['source']
                cur_line = edge['line']
                cur_rush_time = edge['rush_cost']
                cur_cost_time = edge['ride_cost'] + edge['rush_cost']
            # 如果到最后，那么要输出最后一段
            if index == len(path) - 1:
                cur_end = edge['target']
                content += f'在**{cur_start}**站换乘或等车**{round(cur_rush_time / 60)}**分钟，乘坐**{cur_line[:cur_line.find('(')]}**，从**{cur_start}**站坐到**{cur_end}**站，总共花费**{round(cur_cost_time / 60)}**分钟\n\n'

        content += '#### 路线综合信息\n\n'
        content += f'总耗时：{round(path[-1]['time_cost'] / 60)}分钟\n\n'
        content += f'到达时间：{path[-1]['time'].hour}时{path[-1]['time'].minute}分\n\n'
        content += f'总距离：{path[-1]['distance_cost'] / 1000}公里\n\n'
        return content

    # 识别用户意图
    station_from = None
    station_to = None
    strategy_list = []

    station_select = '|'.join(station_name for station_name in station_list)

    # 识别起始站
    match = re.search(r'从(' + station_select + ')', prompt)
    if match:
        station_from = match.group(1)
    # 识别终点站
    match = re.search(r'到(' + station_select + ')', prompt)
    if match:
        station_to = match.group(1)
    # 识别策略
    match = re.findall(r'(最短时间|最少换乘|最短距离)', prompt)
    strategy_list = match

    if station_from is None:
        reply('没有识别到你的起点站哦')
    elif station_data.get(station_from) is None:
        reply(f'"{station_from}"不存在哦')
    elif station_to is None:
        reply('没有识别到你要去的终点站哦')
    elif station_data.get(station_to) is None:
        reply(f'"{station_to}"不存在哦')
    else:
        if len(strategy_list) == 0:
            strategy_list = ['最短时间', '最少换乘', '最短距离']

        strategy_dict = {
            '最短时间': Strategy.BEST_TIMES,
            '最少换乘': Strategy.MINIMAL_TRANSFERS,
            '最短距离': Strategy.SHORTEST_DISTANCE
        }
        response = ''
        for strategy in strategy_list:
            strategy = strategy_dict[strategy]
            path = dijkstra_solve(datetime.now(), station_from, station_to, strategy)
            if path is None:
                st.toast('末班车赶不上了', icon='❗')
                response += f'### 从{station_from}到{station_to}的{strategy}路线:\n\n末班车赶不上了，明天再来吧\n\n'
            else:
                response += generate_path_content(station_from, station_to, strategy, path) + '\n\n'
        reply(response)
