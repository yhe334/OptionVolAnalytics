from typing import Optional

class Cache:
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError
    
