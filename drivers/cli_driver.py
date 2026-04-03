"""
CLI外壳驱动 - 命令行界面
"""

import sys
import shlex
from .agent import DriverInterface


class CLIDriver(DriverInterface):
    """命令行驱动"""
    
    def __init__(self):
        self.history = []
    
    def send_message(self, content: str) -> None:
        """打印消息"""
        print(content)
    
    def send_image(self, path: str) -> None:
        """打印图片路径"""
        print(f"[图片: {path}]")
    
    def send_file(self, path: str) -> None:
        """打印文件路径"""
        print(f"[文件: {path}]")
    
    def get_input(self, prompt: str = "") -> str:
        """获取输入"""
        try:
            return input(prompt)
        except EOFError:
            return ""
    
    def show_loading(self, message: str = "处理中..."):
        """显示加载"""
        print(f"⏳ {message}...")
        class LoadingCtx:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                print("✅ 完成")
        return LoadingCtx()
    
    def toast(self, message: str, duration: int = 3) -> None:
        """显示提示"""
        print(f"📢 {message}")
    
    def set_title(self, title: str) -> None:
        """设置标题（CLI下无效）"""
        pass
    
    def input(self, prompt: str = "") -> str:
        """获取输入"""
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\n再见!")
            sys.exit(0)
