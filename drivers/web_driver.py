"""
Web外壳驱动 - 基于PyWebIO
"""

from pywebio.output import put_text, put_html, put_image, put_file, toast
from pywebio.input import input, textarea, input_group
from pywebio import config
from .agent import DriverInterface


class WebDriver(DriverInterface):
    """PyWebIO Web驱动"""
    
    def __init__(self, title: str = "AgentCore AI"):
        self.title = title
    
    def send_message(self, content: str) -> None:
        """发送消息"""
        put_text(content)
    
    def send_html(self, html: str) -> None:
        """发送HTML"""
        put_html(html)
    
    def send_image(self, path: str) -> None:
        """发送图片"""
        put_image(path)
    
    def send_file(self, path: str, name: str = None) -> None:
        """发送文件"""
        with open(path, 'rb') as f:
            data = f.read()
        put_file(name or path, data)
    
    def get_input(self, prompt: str = "") -> str:
        """获取输入"""
        return input(prompt)
    
    def get_textarea(self, prompt: str = "", **kwargs) -> str:
        """获取多行文本"""
        return textarea(prompt, **kwargs)
    
    def show_loading(self, message: str = "处理中..."):
        """显示加载（PyWebIO不支持，返回上下文管理器）"""
        return toast(message, duration=-1)
    
    def toast(self, message: str, duration: int = 3) -> None:
        """显示提示"""
        toast(message, duration=duration)
    
    def set_title(self, title: str) -> None:
        """设置标题"""
        self.title = title
