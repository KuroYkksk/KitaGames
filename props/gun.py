import random

class Gun:
    def __init__(self, chamber_size=6):
        self.chamber_size = chamber_size
        self.bullets = [None] * chamber_size
        self.current_position = 0

    def load(self, num_live):
        """装入指定数量的实弹"""
        self.load_bullets(num_live, 'live')

    def load_bullets(self, num, bullet_type):
        """在空膛室装入指定数量的类型子弹（增量装填）"""
        count = 0
        # 先尝试替换已有空位
        for i in range(self.chamber_size):
            if count >= num:
                break
            if self.bullets[i] is None:
                self.bullets[i] = bullet_type
                count += 1
        
        # 如果还有剩余数量且弹仓未满，扩展装填（处理初始化空弹仓的情况）
        remaining = num - count
        if remaining > 0 and len(self.bullets) < self.chamber_size:
            add = min(remaining, self.chamber_size - len(self.bullets))
            self.bullets += [bullet_type] * add
            count += add
        
        # 确保不超过弹仓容量
        self.bullets = self.bullets[:self.chamber_size]

    def spin(self):
        random.shuffle(self.bullets)
        self.current_position = 0

    def fire(self):
        """击发并返回弹药类型"""
        if not self.bullets or self.current_position >= len(self.bullets):
            return None
        bullet = self.bullets[self.current_position]
        self.bullets[self.current_position] = None
        self.current_position = (self.current_position + 1) % self.chamber_size
        return bullet

    def has_ammo(self) -> bool:
        """检查是否有剩余弹药"""
        return any(bullet is not None for bullet in self.bullets)

    def __repr__(self):
        return f"Gun(chamber_size={self.chamber_size}, bullets={self.bullets})"