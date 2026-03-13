"""
Redis 缓存客户端
"""

import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 缓存客户端"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.db = settings.REDIS_DB
        self.password = settings.REDIS_PASSWORD
        
        # 缓存键前缀
        self.prefix = "fire_eye:"
    
    async def connect(self) -> None:
        """建立 Redis 连接"""
        try:
            self.redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # 验证连接
            await self.redis.ping()
            logger.info("Redis 缓存连接成功")
            
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            raise
    
    async def disconnect(self) -> None:
        """关闭 Redis 连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis 缓存连接已关闭")
    
    def _get_key(self, key: str) -> str:
        """获取带前缀的缓存键"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            value = await self.redis.get(self._get_key(key))
            if value is None:
                return None
            
            # 尝试解析 JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"获取缓存失败: {key}, 错误: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """设置缓存值"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            # 设置过期时间
            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire
            
            result = await self.redis.set(
                self._get_key(key),
                serialized_value,
                ex=expire_seconds
            )
            return result
            
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            result = await self.redis.delete(self._get_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            result = await self.redis.exists(self._get_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {key}, 错误: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            result = await self.redis.expire(self._get_key(key), seconds)
            return result
        except Exception as e:
            logger.error(f"设置缓存过期时间失败: {key}, 错误: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            result = await self.redis.incrby(self._get_key(key), amount)
            return result
        except Exception as e:
            logger.error(f"递增计数器失败: {key}, 错误: {e}")
            return None
    
    async def get_hash(self, key: str, field: str) -> Optional[Any]:
        """获取哈希字段值"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            value = await self.redis.hget(self._get_key(key), field)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"获取哈希字段失败: {key}.{field}, 错误: {e}")
            return None
    
    async def set_hash(self, key: str, field: str, value: Any) -> bool:
        """设置哈希字段值"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            result = await self.redis.hset(
                self._get_key(key),
                field,
                serialized_value
            )
            return result > 0
            
        except Exception as e:
            logger.error(f"设置哈希字段失败: {key}.{field}, 错误: {e}")
            return False
    
    async def get_all_hash(self, key: str) -> Optional[dict]:
        """获取整个哈希"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            result = await self.redis.hgetall(self._get_key(key))
            if not result:
                return None
            
            # 尝试解析 JSON 值
            parsed_result = {}
            for field, value in result.items():
                try:
                    parsed_result[field] = json.loads(value)
                except json.JSONDecodeError:
                    parsed_result[field] = value
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"获取哈希失败: {key}, 错误: {e}")
            return None
    
    async def push_to_list(self, key: str, value: Any) -> Optional[int]:
        """向列表推送值"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = str(value)
            
            result = await self.redis.lpush(self._get_key(key), serialized_value)
            return result
            
        except Exception as e:
            logger.error(f"推送到列表失败: {key}, 错误: {e}")
            return None
    
    async def pop_from_list(self, key: str) -> Optional[Any]:
        """从列表弹出值"""
        if not self.redis:
            raise RuntimeError("Redis 客户端未初始化")
        
        try:
            value = await self.redis.rpop(self._get_key(key))
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            logger.error(f"从列表弹出失败: {key}, 错误: {e}")
            return None


# 全局 Redis 客户端实例
redis_client = RedisClient()