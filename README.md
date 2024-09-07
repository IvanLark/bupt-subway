# 如何运行
本程序使用`streamlit`作为webui，运行`webui.bat`即可打开浏览器界面。

# 程序介绍
北邮数据结构小学期作业-地铁问题

## 问题描述
当一个用户从甲地到乙地时，由于不同需求，就有不同的交通路线，有人希望以最短时间到达，有人希望用最少的换乘次数等。请编写一北京地铁线路查询系统，通过输入起始站、终点站，为用户提供两种决策的交通咨询。

## 设计要求
1.	提供对地铁线路进行编辑的功能，要求可以添加或删除线路。
2.	提供两种决策：最短时间，最少换乘次数。
3.	中途换乘站换乘耗时为5分钟，地铁在除始发站外每一站停留1分钟。
4.	按照始发站时间、地铁时速及停留时间推算之后各个线路的地铁到站时间。
5.	该系统以人机对话方式进行。系统自动获取当前时间，用户输入起始站，终点站以及需求原则（需求原则包括最短距离，最短时间，最少换乘次数），系统输出乘车方案：乘几号线，距离，时间，费用，换乘方法等相关信息。

# 算法介绍
Dijkstra

