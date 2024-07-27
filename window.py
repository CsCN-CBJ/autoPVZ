import win32gui
from dataclasses import dataclass
import pyautogui
import cv2
import numpy as np


@dataclass(init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False)
class Point:
    """
    二维坐标点类 用于记录坐标点的x和y坐标
    支持的操作: Point +- Point, Point +- Sequence(使用下标0, 1分别代表x, y)
    整数乘除, 作为Sequence或iterable
    """
    x: int
    y: int

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            return Point(self.x + other[0], self.y + other[1])

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        else:
            return Point(self.x - other[0], self.y - other[1])

    def __mul__(self, other: int):
        if isinstance(other, int):
            return Point(self.x * other, self.y * other)
        raise ValueError("Locate can only __mul__ int")

    def __floordiv__(self, other):
        if isinstance(other, int):
            return Point(self.x // other, self.y // other)
        raise ValueError("Locate can only __floordiv__ int")

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        else:
            return None

    def __len__(self):
        # 一些函数会判断这个实例的长度, 写这个函数就可以把这个类当做iterable来用
        return 2

    # 实现*locate传递参数的功能
    def __iter__(self):
        return iter([self.x, self.y])


class Screen:
    """
    屏幕类, 实现了对某个应用程序窗口的简单控制与管理
    """

    def __init__(self, left, top, width, height):
        self.baseLocate = Point(left, top)
        self.size = Point(width, height)

    def mouseInScreen(self) -> bool:
        """
        检查鼠标是否还在指定的用户区域中
        """
        x, y = pyautogui.position()
        return \
            self.baseLocate.x <= x <= self.baseLocate.x + self.size.x and \
            self.baseLocate.y <= y <= self.baseLocate.y + self.size.y

    def Shot(self):
        """
        获取用户界面的截图, 截全屏之后分段选取, 防止跑出去, 减少计算量
        :return: np.ndarray
        """
        sc = pyautogui.screenshot()
        sc_cv = cv2.cvtColor(np.array(sc), cv2.COLOR_RGB2BGR)
        # size = self.image.shape[:2]
        corner = self.baseLocate + self.size
        return sc_cv[self.baseLocate.y:corner.y, self.baseLocate.x:corner.x]


def getWindowRect(className, titleName):
    """
    获取某个窗口边框以内的范围
    可以去看我写的python那里的教程, 知道如何获取className和titleName(使用spyxx_amd64.exe)
    :param className 类名
    :param titleName 标题名
    :return: left, top, width, height
    """
    # 获取窗口句柄
    hwnd = win32gui.FindWindow(className, titleName)
    if hwnd is None:
        raise Exception("没有找到窗口")

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)  # 这个是整个窗口的四角位置, 带白边
    _, _, width, height = win32gui.GetClientRect(hwnd)  # 这个是窗口不带白边的大小

    # 计算窗口边框的宽度和高度
    border_width = (right - left - width) // 2
    titlebar_height = bottom - top - height - border_width

    # 调整窗口客户区坐标以去除边框
    left += border_width
    right -= border_width
    top += titlebar_height
    bottom -= border_width

    return left, top, width, height
