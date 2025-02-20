import re
import random
from bot_manager import BotManager as bot
from base.game_base import GameBase
from props.gun import Gun

GAME_ID = "ruro"
GAME_CLASS = "RussianRouletteGame"

class RussianRouletteGame(GameBase):
    MAX_PLAYERS = 6
    MAX_SILENCE_MINUTES = 1
    
    def __init__(self, group_id):
        super().__init__(group_id)
        self.gun = Gun()
        self.gun.load(1)  # 装填1发实弹
        self.gun.spin()   # 初始旋转弹仓

    def handle_custom_command(self, user_id, command, args):
        if command == "fire":
            self.handle_fire(user_id)

    def handle_fire(self, user_id):
        if not self.is_started:
            bot.send_group("游戏还没开始呢～先喊start才能扣扳机哦！🔫💤", self.group_id)
            return
            
        if user_id != self.player_list[self.current_player]:
            bot.send_group("还没轮到你的回合！别抢戏啦～🎭", self.group_id)
            return

        bullet_type = self.gun.fire()
        msg = (
            f"【俄罗斯轮盘】第{self.turn}回合\n"
            "======================\n"
            f"{user_id}扣动了扳机...💥\n"
        )

        if bullet_type == 'live':
            msg += "实弹击发！！\n"
            print(f"mute: {user_id} {self.MAX_SILENCE_MINUTES}分钟")
            msg += f"玩家{user_id} 被禁言{self.MAX_SILENCE_MINUTES}分钟😵"
            self._end_game()
        else:
            msg += "咔嗒——空枪！\n"
            self._next_turn()
            msg += f"下一个玩家：{bot.at_user(self.player_list[self.current_player])}"

        bot.send_group(f"{msg}", self.group_id)

    def _next_turn(self):
        self.next_player()
        if self.current_player == 0:
            self.next_turn()
            
        # 检查弹药是否耗尽
        if not self.gun.has_ammo():
            self._end_game()

    def _end_game(self):
        end_msg = (
            "所有弹药击发完毕！\n"
            "======================\n"
            "游戏结束～大家快去安慰受伤的鼓手吧！🥁💔"
        )
        bot.send_group(f"{end_msg}", self.group_id)
        self.reset()

    def start(self):
        super().start()
        self.shuffle_players()
        start_msg = (
            "【心跳~俄罗斯轮盘】游戏开始！\n"
            "======================\n"
            f"弹仓容量：{self.gun.chamber_size}发（实弹1发）\n"
            f"玩家顺序：{', '.join(map(str, self.player_list))}\n"
            "======================\n"
            f"首先由玩家{bot.at_user(self.player_list[0])}开始！"
        )
        bot.send_group(f"{start_msg}", self.group_id)