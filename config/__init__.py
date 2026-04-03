# 驱动接口 - 定义标准协议
from abc import ABC, abstractmethod
from typing import Any, Optional


class DriverInterface(ABC):
    """
    外壳驱动标准接口
    所有外壳驱动必须实现此接口
    """
    
    @abstractmethod
    def send_message(self, content: str, **kwargs) -> None:
        """发送文本消息给用户"""
        pass
    
    @abstractmethod
    def send_image(self, path: str, **kwargs) -> None:
        """发送图片给用户"""
        pass
    
    @abstractmethod
    def send_file(self, path: str, **kwargs) -> None:
        """发送文件给用户"""
        pass
    
    @abstractmethod
    def get_input(self, prompt: str = "", **kwargs) -> str:
        """获取用户输入"""
        pass
    
    @abstractmethod
    def show_loading(self, message: str = "处理中...") -> Any:
        """显示加载状态"""
        pass
    
    @abstractmethod
    def toast(self, message: str, duration: int = 3) -> None:
        """显示提示消息"""
        pass
    
    def save_file(self, content: Any, path: str) -> str:
        """保存文件（通用实现）"""
        import json
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False, indent=2)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(content))
        return path
    
    def load_file(self, path: str) -> Any:
        """读取文件（通用实现）"""
        import json
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        try:
            return json.loads(content)
        except:
            return content
