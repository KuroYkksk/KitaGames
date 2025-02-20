import sys
from pathlib import Path
from typing import List
import re
import random
from datetime import timedelta

# 动态添加项目根目录到Python路径
_current_dir: Path = Path(__file__).parent.resolve()
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# 第三方库导入
from hoshino import Service, util, priv
from hoshino.typing import CQEvent

# 本地模块导入
from manager.game_manager import GameManager
import bot_manager

sv = Service('kita_game')

gameManager = GameManager()

@sv.on_prefix('/')
async def game63_join(bot, ev):
    print(ev.user_id, ev.group_id, ev.message.extract_plain_text())
    gameManager.handle_message(ev.user_id, ev.group_id, ev.message.extract_plain_text())
    bot_manager._bot = bot
