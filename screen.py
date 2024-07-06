import typing

import cv2
from cbjLibrary.window import *
import numpy as np
import pyautogui
from typing import Optional

FIRST_CARD_OFFSET = Point(79, 7)  # 第一张卡片的左上角
# FIRST_CARD_OFFSET = Point(89, 7)  # 第一张卡片的左上角
CARD_SIZE = Point(55, 70)

FIRST_GRASS_OFFSET = Point(80, 130)  # 第一个草皮的中间位置
GRASS_SIZE = Point(80, 100)

PVZ_SIZE = Point(800, 600)
ZOMBIE_HEIGHT = 70


class PvzScreen(Screen):
    def getCardCorner(self, index: int) -> Point:
        """
        获取第几个卡片的左上角位置 相对于pvz界面
        :param index: 卡片序号, 0-9
        :return: Locate
        """
        # 每个卡牌之间有空隙, 故50+1
        return Point(FIRST_CARD_OFFSET.x + (CARD_SIZE.x + 1) * index, FIRST_CARD_OFFSET.y)

    def getCardCenter(self, index: int) -> Point:
        """
        获取第几个卡片的中心点位置 相对于pvz界面
        :param index: 卡片序号, 0-9
        :return: Locate
        """
        corner = self.getCardCorner(index)
        return corner + CARD_SIZE // 2

    def getGrass(self, row, col) -> Point:
        """
        获取草坪上的种植位置 相对于pvz界面
        :param row: 行 0-4/5
        :param col: 列 0-8
        :return: Locate
        """
        p = Point(0, 0)
        p += FIRST_GRASS_OFFSET
        p.x += col * GRASS_SIZE.x
        p.y += row * GRASS_SIZE.y
        return p

    def cardAvailable(self, image, index: int) -> bool:
        """
        检查某张卡片是否可以使用
        只判断了卡片所在方框的灰度, 阳光可能对此有一定影响
        :param image: 当前pvz图片
        :param index: 卡片所在卡槽0-9
        :return: 卡片是否可以使用
        """
        left, top = self.getCardCorner(index)
        width, height = CARD_SIZE
        # 阳光挡住的情况
        # if pyautogui.locate(f"./data/{index}.jpg", image) is None:
        #     return False
        return np.mean(image[top:top + height, left:left + width]) > 100

    def zombieRow(self, top) -> int:
        top += ZOMBIE_HEIGHT - FIRST_GRASS_OFFSET.y
        return round(top / GRASS_SIZE.y)


def getBoxCenter(box) -> Point:
    """
    获取box对象的中心点
    :param box: Box(left, top, width, height)
    :return: 中心点Point
    """
    return Point(box.left + box.width // 2, box.top + box.height // 2)


def locateCenter(target, image, confidence=0.7) -> Optional[Point]:
    """
    获取中心点坐标 绝对坐标
    :param target:
    :param image:
    :param confidence:
    :return:
    """
    lo = pyautogui.locate(target, image, confidence=confidence)
    if lo is None:
        return None
    left, top, width, height = lo
    return Point(left, top) + (width // 2, height // 2)


def locateAllCenter(target, image, confidence=0.7) -> list[Point]:
    """
    定位所有指定图像, 并去除重合的图像
    :return: List[Box(left, top, width, height)]
    """
    boxes = pyautogui.locateAll(target, image, confidence=confidence)
    now = next(boxes, None)  # 当前的坐标点, 用来判断图像是否重合
    if now is None:
        return []
    result = [getBoxCenter(now)]  # 结果数组, 识别为不重合的坐标点都放到这里面来
    width, height = now.width, now.height

    for box in boxes:
        # 重合的图像直接跳过
        if abs(now.left - box.left) < width and abs(now.top - box.top) < height:
            continue

        # 不重合的坐标点都放到这里面来
        result.append(getBoxCenter(box))
        now = box

    return result
