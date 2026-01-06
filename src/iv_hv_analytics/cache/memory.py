import time
from typing import Optional,Dict,Tuple
from iv_hv_analytics.cache.base import Cache    

class MemoryCache(Cache):
    def __init__(self) -> None:
        # key -> (expires_at, value)
        self.__store: Dict[str,Tuple[float,str]] = {}

    def get(self, key: str) -> Optional[str]:
        item = self.__store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() > expires_at:    
            self.__store.pop(key,None)
            return None
        return value
    
    def set(self, key: str, value: str, ttl_seconds:int) -> None:
        self.__store[key] = (time.time() + ttl_seconds, value)
