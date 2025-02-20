import time
import asyncio

_bot = None

class BotManager:
    @staticmethod
    def send_group(msg, group_id):
        print(f"[发送消息：群聊 {group_id}] > {msg}")
        if _bot is None:
            print('Bot has not been initialized')
            return
        asyncio.run_coroutine_threadsafe(_bot.send_group_msg(group_id=group_id, message=msg), _bot.loop)
        return msg
    
    @staticmethod
    def send_private(msg, user_id):
        print(f"[发送消息：私聊 {user_id}] > {msg}")
        if _bot is None:
            print('Bot has not been initialized')
            return
        asyncio.run_coroutine_threadsafe(_bot.send_group_msg(user_id=user_id, message=msg), _bot.loop)
        return msg
    
    @staticmethod
    def at_user(user_id):
        print(f"[@] > {user_id}")
        cq_at = f"[CQ:at,qq={user_id}]"
        return cq_at
    
    @staticmethod
    def mute_user(user_id, group_id, duration):
        print(f"[群聊 {group_id} -> {user_id}] 禁言 {duration}")
        if _bot is None:
            print('Bot has not been initialized')
            return
        asyncio.run_coroutine_threadsafe(_bot.set_group_ban(group_id=group_id, user_id=user_id, duration=duration), _bot.loop)

    @staticmethod
    def block_user(user_id, group_id, duration):
        print(f"[群聊 {group_id} -> {user_id}] 拉黑 {duration}")