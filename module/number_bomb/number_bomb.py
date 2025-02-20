import re
import random
from base.game_base import GameBase

GAME_ID = "bomb"
GAME_CLASS = "NumberBombGame"

class NumberBombGame(GameBase):
    MAX_PLAYERS = 6  # 默认最大玩家数
    MAX_SILENCE_MINUTES = 3
    
    def __init__(self, group_id):
        super().__init__(group_id)
        self.min_num = 1
        self.max_num = 100
        self.bomb = -1

    def handle_custom_command(self, user_id, command, args):
        if re.fullmatch(r'\d+', command):
            self.handle_guess(user_id, [command] + args)  # 将数字作为第一个参数
        else:
            print(f"未知指令: {command}")

    # /bomb start
    def start(self):
        super().start()
        
        # 游戏初始化
        self.shuffle_players()
        self.bomb = random.randrange(2, 100)
        self.min_num = 1
        self.max_num = 100
        
        init_hint = (
            "【心跳~禁言数字炸弹】游戏开始\n"
            "======================\n"
            f"Bomb已生成~【1】—>【100】\n"
            "======================\n"
            f"首先由玩家{self.player_list[0]}猜数"
        )
        print(f"send: {init_hint}")
        print(f"bomb: {self.bomb}")

    # /bomb reset
    def reset(self):
        super().reset()
        # 重置游戏数据
        self.min_num = 1
        self.max_num = 100
        self.bomb = -1

        # 处理强制重置条件
        if self.max_num - self.min_num <= 4:
            self._force_reset()
            return

        print("send: 炸弹已解除，游戏完全重置")

    # /bomb 50
    def handle_guess(self, user_id, args):
        if not self.is_started:
            print("send: 游戏尚未开始")
            return
        
        # 验证当前玩家
        if user_id != self.player_list[self.current_player]:
            print("send: 还没轮到你啦！先给主唱大人打call吧～💃📢")
            return
        
        try:
            guess = int(args[0])
        except (IndexError, ValueError):
            print("send: 请输入有效数字，例如/bomb 50")
            return
        
        if not (self.min_num < guess < self.max_num):
            print(f"send: 数字超出范围（当前范围：{self.min_num}-{self.max_num}）")
            return
        
        if guess == self.bomb:
            self._handle_explosion(user_id)
        else:
            self._update_range(guess)

    def _handle_explosion(self, user_id):
        min_mute = 1 if self.turn > 1 else self.MAX_SILENCE_MINUTES
        print(f"mute: {user_id} {min_mute}分钟")
        
        bomb_hint = (
            "Boom————\t游戏结束\n"
            "===================\n"
            f"[CQ:face,id=55][CQ:face,id=55]—>【{self.bomb}】<—[CQ:face,id=55][CQ:face,id=55]\n"
            "===================\n"
            f"玩家{user_id} 被禁言{min_mute}分钟"
        )
        print(f"send: {bomb_hint}")
        self.reset()

    def _update_range(self, guess):
        # 更新数字范围
        if guess < self.bomb:
            self.min_num = guess
        else:
            self.max_num = guess
        
        # 轮换玩家
        self.next_player()
        if self.current_player == 0:
            self.next_turn()
        
        hint = (
            f"Turn({self.turn}): \t\tM I S S\n"
            "===============\n"
            f"Hint: 【{self.min_num}】—>【{self.max_num}】\n"
            "===============\n"
            f"轮到玩家{self.player_list[self.current_player]}猜数"
        )
        print(f"send: {hint}")

    def _force_reset(self):
        print(f"mute: {self.player_list[self.current_player]} 3分钟")
        hint = (
            "英雄可不能临阵逃脱啊！\n"
            "===================\n"
            f"[CQ:face,id=55]——>【{self.bomb}】<——[CQ:face,id=55]\n"
            "===================\n"
            f"玩家{self.player_list[self.current_player]} 被禁言3分钟"
        )
        print(f"send: {hint}")
        self.reset()
