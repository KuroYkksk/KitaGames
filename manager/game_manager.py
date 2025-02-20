# game_manager/game_manager.py
from importlib import import_module
from config.game_module import GAME_MODULES
from message.message_sender import MessageSender as sender

# 预加载所有游戏模块
GAME_CLASSES = {}  # 存储game_id对应的游戏类
GAME_ID_LIST = []  # 存储所有有效的game_id

for module_name in GAME_MODULES:
    try:
        module = import_module(f'module.{module_name}')

        # 获取游戏元数据
        game_id = getattr(module, 'GAME_ID', None)
        game_class_name = getattr(module, 'GAME_CLASS', None)

        if not game_id:
            print(f"模块 {module_name} 缺少 GAME_ID 定义，跳过加载")
            continue
        if not game_class_name:
            print(f"模块 {module_name} 缺少 GAME_CLASS 定义，跳过加载")
            continue

        # 获取游戏类对象
        game_class = getattr(module, game_class_name, None)
        if not game_class:
            print(f"模块 {module_name} 中找不到类 {game_class_name}")
            continue

        # 存储到全局
        GAME_CLASSES[game_id] = game_class
        GAME_ID_LIST.append(game_id)
        print(f"成功加载游戏: ID={game_id}")
        
    except ImportError as e:
        print(f"无法加载模块 {module_name}: {str(e)}")
    except Exception as e:
        print(f"加载 {module_name} 时发生意外错误: {str(e)}")

class GameManager:
    def __init__(self):
        self.game_list = {}  # 结构: {groupId: {gameId: game_instance}}

    def handle_message(self, userId, groupId, message):
        """处理消息入口"""
        if message.startswith('/'):
            command_part = message[1:].lstrip()
            if not command_part:  # 处理空命令的情况（如消息仅为"/"）
                return
            # 分割命令和参数
            split_result = command_part.split(maxsplit=1)
            game_id = split_result[0]
            command_message = split_result[1] if len(split_result) > 1 else ''

            if game_id in GAME_ID_LIST:
                self.init_game(groupId, game_id)
                # 获取游戏实例并处理消息
                if groupId in self.game_list and game_id in self.game_list[groupId]:
                    game_instance = self.game_list[groupId][game_id]
                    game_instance.handle_message(userId, command_message)
                
    def init_game(self, groupId: str, gameId: str):
        """初始化游戏实例"""
        # 检查是否已存在相同gameId
        if groupId in self.game_list and gameId in self.game_list[groupId]:
            print(f"游戏 {gameId} 已在该群存在")
            return
            
        # 检查游戏是否已加载
        if gameId not in GAME_CLASSES:
            print(f"游戏 {gameId} 未启用或加载失败")
            return
        
        try:
            # 从预加载的类中实例化
            game_class = GAME_CLASSES[gameId]
            game_instance = game_class(groupId)
        except Exception as e:
            print(f"初始化失败: {e}")
            return
            
        # 保存实例
        if groupId not in self.game_list:
            self.game_list[groupId] = {}
        self.game_list[groupId][gameId] = game_instance
        print(f"已为群组 {groupId} 创建游戏 {gameId}")
        self._show_game_list()
        
    def _show_game_list(self):
        """显示当前游戏列表"""
        print("当前运行的游戏列表：")
        for group, games in self.game_list.items():
            print(f"群组 {group}: {', '.join(games.keys())}")