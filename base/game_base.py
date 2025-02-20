import random
from abc import ABC, abstractmethod

GAME_ID = "base"
GAME_CLASS = "GameBase" 

class GameBase(ABC):
    MAX_PLAYERS = 4  # 默认最大玩家数

    def __init__(self, group_id):
        self.group_id = group_id
        self.player_list = []
        self.current_player = 0
        self.turn = 0
        self.is_started = False

    def handle_message(self, user_id, message):
        parts = message.strip().split()
        if not parts:
            return
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command == 'help':
            self.help()
        elif command == 'join':
            self.join(user_id)
        elif command == 'quit':
            self.quit(user_id)
        elif command == 'start':
            self.start()
        elif command == 'reset':
            self.reset()
        elif command == 'info':
            self.info()
        else:
            self.handle_custom_command(user_id, command, args)

    def handle_custom_command(self, user_id, command, args):
        pass

    def help(self):
        help_text = """可用指令：
help - 查看帮助
join - 加入游戏
quit - 退出游戏
start - 开始游戏
reset - 重置游戏
info - 查看游戏状态
其他指令由具体游戏实现"""
        print(f"send: {help_text}")

    def join(self, user_id):
        if self.is_started:
            print("send: 游戏高速运转中！等这局结束再冲进来嘛～🎮⏳")
            return
        if len(self.player_list) >= self.MAX_PLAYERS:
            print("send: 满员MAX！挤不下啦～下次要更快哦！💨")
            return
        if user_id in self.player_list:
            print(f"send: 重复报名禁止！波奇酱会吓到发抖的啦～😱")
            return
        self.player_list.append(user_id)
        print(f"send: 欢迎{user_id}酱加入！一起rock起来吧～🎸✨")

    def quit(self, user_id):
        if user_id not in self.player_list:
            print(f"send: 取消失败！小喜多没找到你的报名表哦～📋💦")
            return
        if self.is_started:
            print("send: 车门焊死！谁都不许临阵脱逃哦～🔧🔥")
            return
        self.player_list.remove(user_id)
        print(f"send: {user_id}酱跳车成功…呜哇！别丢下我们呀～😭")

    def start(self):
        if self.is_started:
            print("send: 已经开飙了啦，车门关死啦～🚗💨")
            return
        if len(self.player_list) < 1:
            print("send: 人数不够啦！至少要凑齐结束乐队四人组嘛～🎤🎸🥁")
            return
        self.is_started = True
        self.turn = 1
        self.current_player = 0
        players = ", ".join(map(str, self.player_list))
        print(f"send: 游戏开始！当前回合：1，玩家顺序：{players}")

    def reset(self):
        self.player_list = []
        self.current_player = 0
        self.turn = 0
        self.is_started = False
        print("send: 游戏已重置")

    def info(self):
        status = "已开始" if self.is_started else "未开始"
        players = "玩家列表：" + ", ".join(map(str, self.player_list)) if self.player_list else "无玩家"
        current_info = ""
        if self.is_started:
            current_info = f"当前回合：{self.turn}"
            if self.player_list:
                current_info += f"，当前玩家：{self.player_list[self.current_player]}"
        msg = f"游戏状态：{status}\n{players}\n{current_info}"
        print(f"send: {msg}")

    def shuffle_players(self):
        random.shuffle(self.player_list)
        print(f"send: 玩家顺序已打乱：{', '.join(map(str, self.player_list))}")

    def next_player(self):
        if not self.player_list:
            return
        self.current_player = (self.current_player + 1) % len(self.player_list)
        print(f"send: 当前轮到玩家{self.player_list[self.current_player]}")

    def next_turn(self):
        self.turn += 1
        print(f"send: 进入第{self.turn}回合")