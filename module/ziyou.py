import pytz
from datetime import datetime, timedelta
import re
import random

from hoshino import R, Service, util, priv
from hoshino.typing import CQEvent
from ... import pic_generator

sv = Service('fake_dice')
tz = pytz.timezone('Asia/Shanghai')

MAX_PLAYER = 6
MAX_SILENCE_MINUTES = 5

# 全局变量
_is_ziyou_start = False
player_list = list()
_current_player = 0
_turn = -1

#场况
_diceNum = 0
_diceSize = 0
_zhai = False
_firstCall = True  # 首叫
allDice = list()
dice_mark = list()  # 发骰标记

silence_count = list()  #累计眩晕值
MAX_SILENCE_COUNT = 3
_kick_count = 0


# 生成全场骰子
def setDice():
    for i in range(len(player_list*5)):
        allDice.append(random.randint(1,6))
    return

# 游戏初始化
def ziyou_init():
    global _is_ziyou_start, _turn, _current_player
    global _firstCall, _zhai, _diceNum, _diceSize, _kick_count
    _is_ziyou_start = True
    ###生成玩家列表###
    random.shuffle(player_list)
    _current_player = 0
    _turn = 1

    ### 初始化场况 ###
    _firstCall = True
    _zhai = False
    _diceNum = 0
    _diceSize = 0
    allDice.clear()
    dice_mark.clear()
    setDice()
    _kick_count = 0
    # 初始化眩晕值
    for i in range(len(player_list)):
        silence_count.append(0)
        dice_mark.append(0)

    init_hint = f'【ziyou】(Turn {_turn})\n'\
              + '请[CQ:at,qq=' + str(player_list[0]) + ']宣言'
    return init_hint
    # 玩家列表
    # order = '[CQ:at,qq=' + str(player_list(0)) + ']'
    # for i in range(1, MAX_PLAYER):
    #     order += '->[CQ:at,qq=' + str(player_list(i)) + ']'
    # return order

# 游戏重置
def game_reset():
    print('game reset')
    global _is_ziyou_start, _turn, _current_player
    global _firstCall, _zhai, _diceNum, _diceSize, _kick_count
    _is_ziyou_start = False
    ###重置玩家列表###
    player_list.clear()
    _current_player = 0
    _turn = -1
    
    _firstCall = True
    _zhai = False
    _diceNum = 0
    _diceSize = 0
    allDice.clear()
    _kick_count = 0
    # 重置眩晕值
    silence_count.clear()

# 玩家循环
def next_player():
    global _current_player
    _current_player += 1
    if _current_player == len(player_list):
        _current_player = 0

# 宣言判断
def call_judge(dice_num, dice_size, zhai):
    global _diceNum, _diceSize, _zhai
    global _firstCall
    if dice_size < 1 or dice_size > 6:
        return False
    ## 首叫 ##
    if _firstCall == True:
        _zhai = zhai
        if dice_num < len(player_list):
            return False
        if dice_num == len(player_list):
            if dice_size != 1: 
                return False
            else: 
                _zhai = True
        if dice_num == len(player_list)+1:
            _zhai = True
        if dice_size == 1:  # 如果叫1点忘了斋
            _zhai = True
        # 更新场况
        _firstCall = False
        _diceNum = dice_num
        _diceSize = dice_size
        return True
    ## 普通叫 ##
    # 小写为宣言，大写为全局
    temp_size = dice_size
    if temp_size == 1:
        zhai = True     # 如果叫1点忘了斋
        temp_size = 7
    temp_SIZE = _diceSize
    if temp_SIZE == 1:
        temp_SIZE = 7

    if zhai != _zhai:
        if zhai:
            if dice_num < _diceNum-1:   return False
            else:   _zhai = True
        else:
            if dice_num < _diceNum*2:   return False
            else:   _zhai = False
    else:
        if dice_num < _diceNum:    return False
        if dice_num == _diceNum and temp_size <= temp_SIZE: return False
    # 更新场况
    _diceNum = dice_num
    _diceSize = dice_size
    return True

### 宣言反对(劈) ###
async def call_object(bot, ev):
    dice_count = 0  #统计数
    object_hint = f'劈: 【{_diceNum}个{_diceSize}'
    if _zhai:   object_hint += ',斋'
    object_hint += '】\n'
    for i in range(len(player_list)):
        #例[1,2,3,4,5]**:(1/3)PlayerName
        dice_hint, bonus, dice_count = dice_settle(i, dice_count) #骰子统计
        object_hint += dice_hint    #拼接玩家色子
        if bonus: object_hint += '**'  #拼接围色提示
        #拼接玩家id
        game_member = await bot.get_group_member_info(group_id=ev.group_id, user_id=player_list[i])
        game_player = game_member["card"] or game_member["nickname"] or str(player_list[i])
        object_hint += f' :({silence_count[i]}/{MAX_SILENCE_COUNT}){game_player}' + '\n'
    object_hint += f'结果: 【{dice_count}个{_diceSize}】'
    if _zhai:   object_hint += ' '
    else:   object_hint += ' (计1)'
    print(dice_count, object_hint)
    # await bot.send(ev, object_hint)
    object_success = dice_count < _diceNum
    # 眩晕值累加
    loser_index = silence_counter(object_success)   
    loser_member = await bot.get_group_member_info(group_id=ev.group_id, user_id=player_list[loser_index])
    loser_player = loser_member["card"] or loser_member["nickname"] or str(player_list[loser_index])
    if silence_count[loser_index] == MAX_SILENCE_COUNT:
        # 游戏结束
        object_hint += f'\n(Turn {_turn}){loser_player}[寄]:({silence_count[loser_index]}/{MAX_SILENCE_COUNT})'
        if loser_member["role"] == "member":
            await bot.set_group_ban(group_id=ev.group_id, user_id=player_list[loser_index], duration=MAX_SILENCE_MINUTES * 60)
        else:   #拉黑管理员代替禁言
            priv.set_block_user(ev.user_id, timedelta(minutes=MAX_SILENCE_MINUTES))
        game_reset()
    else: 
        # 下一回合
        object_hint += f'\n(Turn {_turn}){loser_player}[喝]:({silence_count[loser_index]}/{MAX_SILENCE_COUNT})'
        next_turn()
        # 分发骰子
        for playerNo in range(0,len(player_list)):
            playerDice = list()
            for diceNo in range(0,5):
                playerDice.append(allDice[5*playerNo+diceNo])
            playerDice.sort()
            # 改为游戏进行中分发
            # await bot.send_private_msg(self_id=ev.self_id, user_id=player_list[playerNo], message=f'dice：{playerDice} ({silence_count[playerNo]}/{MAX_SILENCE_COUNT})')

            ### 透视(debug用) ###
            game_member = await bot.get_group_member_info(group_id=ev.group_id, user_id=player_list[playerNo])
            game_player = game_member["card"] or game_member["nickname"] or str(player_list[playerNo])
            print(playerDice, game_player)
            ###    透视end    ###
            playerDice.clear()
        # 输者起叫
        global _current_player
        _current_player = loser_index
        next_hint = '\n====================\n'\
                + f'【ziyou】(Turn {_turn})骰子更新\n'\
                + f'请{loser_player}宣言'
                #+ '请[CQ:at,qq=' + str(player_list[loser_index]) + ']宣言'
        object_hint += next_hint
        # 分发骰子
        send_dice = list()
        for diceNo in range(0,5):
            send_dice.append(allDice[5*_current_player+diceNo])
        send_dice.sort()
        await bot.send_private_msg(self_id=ev.self_id, \
                                    user_id=player_list[_current_player], \
                                    message=f'dice：{send_dice} ({silence_count[_current_player]}/{MAX_SILENCE_COUNT})')
        dice_mark[_current_player] = 1
    if object_success:   return True, object_hint
    else:   return False, object_hint
#结算(骰子整理)
def dice_settle(index, diceCnt):
    playerDice = list()
    bucket = [0]*6
    for i in range(5):
        playerDice.append( allDice[index*5+i] )
        bucket[ allDice[index*5+i]-1 ] += 1  #-1变索引
    nextCnt, bonus = dice_analysis(bucket)
    diceCnt += nextCnt
    hint = f'{sorted(playerDice)}'
    return hint, bonus, diceCnt
#骰子分析
def dice_analysis(bucket):
    diceCnt = bucket[_diceSize-1]
    bonus = False
    if _zhai:
        if diceCnt == 5:
            diceCnt += 2
            bonus = True
    else:
        if diceCnt == 5 or bucket[0] == 5:
            diceCnt = 7
            bonus = True
        elif diceCnt + bucket[0] == 5:
            diceCnt = 6
            bonus = True
        else:
            diceCnt += bucket[0]
    return diceCnt, bonus

# 眩晕值累计
def silence_counter(object_success):
    temp_index = _current_player    # 获取当前玩家索引
    if object_success:  #如果好劈，上家眩晕值+1
        if temp_index == 0:
            temp_index = len(player_list)
        temp_index -= 1
    silence_count[temp_index] += 1
    return temp_index
# 下一回合
def next_turn():
    global _turn
    global _firstCall, _zhai, _diceNum, _diceSize, _kick_count

    _turn += 1
    ### 仅初始化场况 ###
    _firstCall = True
    _zhai = False
    _diceNum = 0
    _diceSize = 0
    allDice.clear()
    # 清空发骰标记
    for i in range(len(player_list)):
        dice_mark[i] = 0
    setDice()
    _kick_count = 0

    


# 加入游戏
@sv.on_fullmatch('.ziyou join')
async def ziyou_join(bot, ev):
    now = datetime.now(tz)  # 获取时间
    if 2 <= now.hour <= 20:  # 限时开放
        await bot.send(ev, 'ziyou尚未开放')
        return
    if _is_ziyou_start == True:
        await bot.send(ev, 'ziyou已经开始，请等待游戏结束~')
        return
    else:
        if ev.user_id in player_list:
            await bot.send(ev, '请不要重复报名')
            return
        if len(player_list) == MAX_PLAYER:
            await bot.send(ev, '报名失败，玩家已满')
            return
        else:
            # global player_list
            player_list.append(ev.user_id)
            hint = 'ziyou报名成功！\n'\
                 + '===========\n'\
                 + 'Player: ['+ str(len(player_list)) + ' / ' + str(MAX_PLAYER) +']'
            await bot.send(ev, hint)

# 退出游戏
@sv.on_fullmatch('.ziyou quit')
async def ziyou_quit(bot, ev):
    if ev.user_id in player_list:
        if _is_ziyou_start == True:
            await bot.send(ev, '车门焊死，谁都不许跑~')
            return
        player_list.remove(ev.user_id)
        hint = 'ziyou退出成功！\n'\
             + '============\n'\
             + 'Player: ['+ str(len(player_list)) + ' / ' + str(MAX_PLAYER) +']'
        await bot.send(ev, hint)
        return
    else:
        await bot.send(ev, '取消报名失败，你没有报名')
        return

# 开始游戏
@sv.on_fullmatch('.ziyou start')
async def ziyou_start(bot, ev):
    if _is_ziyou_start == True:
        await bot.send(ev, 'ziyou已经开始，请等待游戏结束~')
        return
    if ev.user_id not in player_list:
        await bot.send(ev, '你没有报名，请不要迫害玩家~')
        return
    if len(player_list) < 2:
        await bot.send(ev, 'ziyou开始失败，玩家不足')
    else:
        hint = ziyou_init() 
        print('allDice:', allDice)
        # 分发骰子
        for playerNo in range(0,len(player_list)):
            playerDice = list()
            for diceNo in range(0,5):
                playerDice.append(allDice[5*playerNo+diceNo])
            playerDice.sort()
            # 改为游戏进行中分发
            # await bot.send_private_msg(self_id=ev.self_id, user_id=player_list[playerNo], message=f'dice：{playerDice}')

            ### 透视(debug用) ###
            game_member = await bot.get_group_member_info(group_id=ev.group_id, user_id=player_list[playerNo])
            game_player = game_member["card"] or game_member["nickname"] or str(player_list[playerNo])
            print(playerDice, game_player)
            ###    透视end    ###
            playerDice.clear()
        await bot.send(ev, hint)

    # 分发骰子
    send_dice = list()
    for diceNo in range(0,5):
        send_dice.append(allDice[5*_current_player+diceNo])
    send_dice.sort()
    await bot.send_private_msg(self_id=ev.self_id, \
                                user_id=player_list[_current_player], \
                                message=f'dice：{send_dice} ({silence_count[_current_player]}/{MAX_SILENCE_COUNT})')
    dice_mark[_current_player] = 1

# @sv.on_prefix('b')
@sv.on_rex(r'^[\d]{1,2}个\d斋?$')
async def ziyou_call(bot, ev):
    if _is_ziyou_start == False:
        # await bot.send(ev, 'ziyou尚未开始')
        return
    if (ev.user_id not in player_list) or (ev.user_id != player_list[_current_player]):
        await bot.send(ev, '你未参加游戏，或尚未轮到你的回合')
        return
    diceNum, diceSize = ev.message.extract_plain_text().split('个')
    print('diceSize', diceSize)
    zhai_call = False
    if len(diceSize) == 2:   # 叫斋
        zhai_call = True
    print('call', diceNum, diceSize[0], zhai_call)
    legal_call = call_judge(int(diceNum), int(diceSize[0]), zhai_call)
    if legal_call:
        game_member = await bot.get_group_member_info(group_id=ev.group_id, user_id=player_list[_current_player])
        game_player = game_member["card"] or game_member["nickname"] or str(player_list[_current_player])
        hint = f'#{game_player} : {_diceNum}个{_diceSize}'
        if _zhai:   hint += ',斋'
        next_player()
        global _kick_count
        _kick_count = 0
        hint += f'\n-->[CQ:at,qq={str(player_list[_current_player])}]'
        await bot.send(ev, hint)
        # 继续分发骰子
        if(dice_mark[_current_player]) == 1:
            return  # 判断为发过
        playerDice = list()
        for diceNo in range(0,5):
            playerDice.append(allDice[5*_current_player+diceNo])
        playerDice.sort()
        await bot.send_private_msg(self_id=ev.self_id, \
                                    user_id=player_list[_current_player], \
                                    message=f'dice：{playerDice} ({silence_count[_current_player]}/{MAX_SILENCE_COUNT})')
        dice_mark[_current_player] = 1

    else:
        await bot.send(ev, '宣言不符合规则')

@sv.on_fullmatch('劈')
async def ziyou_object(bot, ev):
    if _is_ziyou_start == False:
        # await bot.send(ev, 'ziyou尚未开始')
        return
    if (ev.user_id not in player_list) or (ev.user_id != player_list[_current_player]):
        await bot.send(ev, '你未参加游戏，或尚未轮到你的回合')
        return
    if _firstCall:
        await bot.send(ev, '当前没有宣言')
        return
    object_success, object_hint = await call_object(bot, ev)
    print('好劈', object_success)
    if object_success:
        object_hint = '好' + object_hint
    else: 
        object_hint = '烂' + object_hint

    # 生成图片
    pic_generator.drawPic(object_hint, ev)
    IMAGE_PATH = 'game_board'
    image = R.img(f'{IMAGE_PATH}/{ev.group_id}.png')
    if _is_ziyou_start:
        await bot.send(ev, f'[CQ:at,qq={str(player_list[_current_player])}]\n{image.cqcode}')
    else:
        await bot.send(ev, f'{image.cqcode}')

@sv.on_fullmatch('单骰')
async def single_dice(bot, ev):
    if _is_ziyou_start == False:
        # await bot.send(ev, 'ziyou尚未开始')
        return
    if (ev.user_id not in player_list):
        # await bot.send(ev, '你未参加游戏，或尚未轮到你的回合')
        return
    single_index = player_list.index(ev.user_id)    # 申请单骰玩家
    bucket = [0]*6
    # 骰子计数
    for i in range(5):
        bucket[ allDice[single_index*5+i]-1 ] += 1
        # 单骰直接返回
        if bucket[ allDice[single_index*5+i]-1 ] > 1:
            await bot.send(ev, '非单骰，驳回😅')
            return
    # 局部重发
    update_dice = list()
    for i in range(5):
        allDice[single_index*5+i] = random.randint(1,6)
        update_dice.append( allDice[single_index*5+i] )
    update_dice.sort()
    print('dice update:', update_dice)
    await bot.send(ev, '牛び')
    await bot.send_private_msg(self_id=ev.self_id, user_id=player_list[single_index], message=f'dice：{update_dice}')


@sv.on_fullmatch('.ziyou reset')
async def ziyou_reset(bot, ev):
    # if _max - _min <= 4:
    #     bomb_member = await bot.get_group_member_info(group_id=ev.group_id, user_id=player_list[_current_player])
    #     bomb_player = bomb_member["card"] or bomb_member["nickname"] or str(player_list[_current_player])
    #     bomb_hint = '英雄可不能临阵逃脱啊！\n'\
    #               + '===================\n'\
    #               + '[CQ:face,id=55]——>【'+ str(_bomb) +'】<——[CQ:face,id=55]\n'\
    #               + '===================\n'\
    #               + '#'+ bomb_player +' 被禁言3分钟'
    #               # + '[CQ:at,qq='+ str(player_list[_current_player]) +']被禁言3分钟'
    #               # + '[CQ:at,qq='+ str(ev.user_id) +']被禁言3分钟'
    #     await bot.send(ev, bomb_hint)
    #     await bot.set_group_ban(group_id=ev.group_id, user_id=player_list[_current_player], duration=MAX_SILENCE_MINUTES * 60)
    #     if ev.user_id != player_list[_current_player]:
    #         await util.silence(ev, MAX_SILENCE_MINUTES * 60, skip_su=False)
    #     game_reset()
    #     return   
    game_reset()
    await bot.send(ev, 'ziyou重置完成！')

@sv.on_fullmatch('.ziyou kick')
async def ziyou_kick(bot, ev):
    if _is_ziyou_start == False:
        # await bot.send(ev, 'ziyou尚未开始')
        return
    if (ev.user_id not in player_list):
        await bot.send(ev, '你未参加游戏，无法投票')
        return
    global _kick_count
    _kick_count +=1
    kick_hint = f'ziyou kick vote: [{_kick_count}/{len(player_list)}]'
    if _kick_count >= len(player_list)/2:
        kick_hint += '\n过半数投票踢出, 游戏结束'
        await bot.set_group_ban(group_id=ev.group_id, user_id=player_list[_current_player], duration=MAX_SILENCE_MINUTES * 60)
        game_reset()
    await bot.send(ev, kick_hint)







@sv.on_fullmatch('.测试图片')
async def test_pic(bot, ev):
    IMAGE_PATH = 'game_board'
    image = R.img(f'{IMAGE_PATH}/{ev.group_id}.png')
    await bot.send(ev, f'{image.cqcode}')