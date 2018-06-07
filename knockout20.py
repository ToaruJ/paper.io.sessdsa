__doc__ = '''单挑赛脚本：读取目录内两个文件，提取play函数并执行'''
import os, sys, time, platform, match_core
from prettytable import PrettyTable
from match_interface import match, save_match_log, clear_storage, swap_storage


# 屏蔽AI自带print
class null_stream:
    def read(*args):
        pass

    def write(*args):
        pass

    def flush(*args):
        pass


sys.stdout = null_stream


# 设置比赛参数
GAMES = 10  # 两两作为先后手各比赛场数，总场次为2*GAMES*n(n-1)
HALFWIDTH = 51
HEIGHT = 101
ROUNDSPERGAME = 2000
TIMELIMIT = 30
CLEAR = 'cls' if platform.system() == 'Windows' else 'clear'    # 根据系统设置清屏指令
FOLDER = 'AI'
players = []


#读取AI文件夹下所有算法
sys.path.append(os.path.abspath(FOLDER))  # 将AI文件夹加入环境路径
for file in os.listdir(FOLDER):
    if file.endswith('.py') and len(players) < 2:
        # 提取play函数
        try:
            name = file[:-3]
            ai = __import__(name)
            ai.play
            players.append((name, ai))

        # 读取时出错
        except Exception as e:
            print('读取%r时出错：%s' % (file, e), file=sys.__stdout__)

# 创建赛程
assert len(players) == 2
name1, func1 = players[0][0], players[0][1]
name2, func2 = players[1][0], players[1][1]


# 根据赛程比赛
# 图形化计分表，比赛结果统计表
x = PrettyTable([' #', 'Endgame Winner', 'Game State', '   Rmk   '])
gameResult = [0, 0]


# 图形化计分表绘图工具
def game_board_outputer(match_result, index, winner,
                        gameResult, name1, name2, x):
    os.system(CLEAR)
    
    flag = match_result['result'][1]
    if flag < 0:
        flag += 8
    rmklst = ['WAL', 'TAP', 'SID', 'FAC', 'CIT', 'END', 'OVT', 'ERR']
    reason = 'KO'
    if flag == 3 or flag == 5:
        reason = str(match_result['result'][-1])

    x.add_row([
        '%2s' % str(index+1), winner, reason,
        rmklst[flag] + ', %4s' % str(len(match_result['log']) - 1)
    ])
    print(
        name1,
        ' ' * (18 - len(name1)),
        str(gameResult[0]),
        ': ',
        str(gameResult[1]),
        ' ' * (20 - len(name2)),
        name2,
        file=sys.__stdout__)
    print(x, file=sys.__stdout__)
    

# 初始化存储空间
storageAB, storageBA = [{}, {}], [{}, {}]
for match_core.STORAGE in storageAB, storageBA:
    for i in range(2):
        try:
            exec('func%d.init(match_core.STORAGE[%d])' % (i + 1, i))
        except:
            pass
storageBA = storageBA[::-1]


for index in range(GAMES):
    # A vs B 顺序存储空间，先赛GAMES局
    match_core.STORAGE = storageAB

    match_result = match((func1, func2), (name1, name2), HALFWIDTH, HEIGHT,
                         ROUNDSPERGAME, TIMELIMIT)
    log_name = '%s/log/%s-VS-%s(%s).zlog' % (FOLDER, name1, name2, 1 + index)
    save_match_log(match_result, log_name)

    gameWinner = match_result['result'][0]
    if gameWinner == 0:
        gameResult[0] += 1
        winner = '(A) ' + name1
    elif gameWinner == 1:
        gameResult[1] += 1
        winner = '(B) ' + name2
    else:
        winner = 'None'
    '''
    终局原因 : 
         0 - WAL 撞墙
         1 - TAP 纸带碰撞
         2 - SID 侧碰
         3 - FAC 正碰，结算得分
         4 - CIT 领地内互相碰撞
        -3 - END 回合数耗尽，结算得分
        -2 - OVT 超时
        -1 - ERR AI函数报错
    '''

    game_board_outputer(match_result, index, winner,
                        gameResult, name1, name2, x)


for index in range(GAMES):
    # B vs A 顺序存储空间，再赛GAMES局
    match_core.STORAGE = storageBA

    match_result = match((func2, func1), (name2, name1), HALFWIDTH, HEIGHT,
                         ROUNDSPERGAME, TIMELIMIT)
    log_name = '%s/log/%s-VS-%s(%s).zlog' % (FOLDER, name2, name1, 1 + i)
    save_match_log(match_result, log_name)

    gameWinner = match_result['result'][0]
    if gameWinner == 1:
        gameResult[0] += 1
        winner = '(B) ' + name1
    elif gameWinner == 0:
        gameResult[1] += 1
        winner = '(A) ' + name2
    else:
        winner = 'None'


    game_board_outputer(match_result, index+10, winner,
                        gameResult, name1, name2, x)


    if gameResult[0] > 10 or gameResult[1] > 10:
        break
    

# 总结函数
storageBA = storageBA[::-1]
for match_core.STORAGE in storageAB, storageBA:
    for i in range(2):
        try:
            exec('func%d.summaryall(match_core.STORAGE[%d])' % (i + 1, i))
        except:
            pass


# 单挑结束，输出结果
if gameResult[0] > gameResult[1]:
    totalresult = name1 + ' wins.'
elif gameResult[0] < gameResult[1]:
    totalresult = name2 + ' wins.'
else:
    totalresult = 'Ties.'
print('Knockout Result:', totalresult, file=sys.__stdout__)
