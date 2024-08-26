from ultralytics import YOLO
import torch
from window import *
import numpy as np
import pyautogui
from typing import Optional

FIRST_CARD_OFFSET = Point(90, 7)  # 第一张卡片的左上角
CARD_SIZE = Point(50, 70)
CARD_INTERVAL = 4

FIRST_GRASS_OFFSET = Point(80, 130)  # 第一个草皮的中间位置
GRASS_SIZE = Point(80, 100)

PVZ_SIZE = Point(800, 600)
ZOMBIE_HEIGHT = 70

model = YOLO("data/zombies.pt")
# 将模型移动到可用的设备上
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


class PvzScreen(Screen):
    cardList: list[str]
    cardImgList: list  # GREY images of cards

    def __init__(self, left, top, width, height, cardList: list[str]):
        super().__init__(left, top, width, height)
        self.cardList = cardList
        self.cardImgList = []
        for name in cardList:
            img = cv2.imread(f"./data/{name}.jpg")
            if img is None:
                raise FileNotFoundError(f"Card {name} not found")
            self.cardImgList.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

    def getCardCorner(self, index: int) -> Point:
        """
        获取第几个卡片的左上角位置 相对于pvz界面
        :param index: 卡片序号, 0-9
        :return: Locate
        """
        # 每个卡牌之间有空隙, 故50+1
        return Point(FIRST_CARD_OFFSET.x + (CARD_SIZE.x + CARD_INTERVAL) * index, FIRST_CARD_OFFSET.y)

    def getCardCenter(self, card) -> Point:
        """
        获取第几个卡片的中心点位置 相对于pvz界面
        :param card: 卡片序号或卡片名称
        :return: Locate
        """
        if type(card) != int:
            card = self.cardList.index(card)
        corner = self.getCardCorner(card)
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

    def cardAvailable(self, image, card) -> bool:
        """
        检查某张卡片是否可以使用
        只判断了卡片所在方框的灰度, 阳光可能对此有一定影响
        :param image: 当前pvz图片
        :param card: 卡片名称或序号
        :return: 卡片是否可以使用
        """
        # 将卡片名称转换为序号
        if type(card) != int:
            card = self.cardList.index(card)
        left, top = self.getCardCorner(card)
        width, height = CARD_SIZE
        cardData = image[top:top + height, left:left + width]

        # 通过灰度判断是否可以使用, 并且判断图片是否一致, 防止有阳光遮挡导致误判
        stdCard = self.cardImgList[card]
        H1 = cv2.calcHist([stdCard], [0], None, [256], [0, 256])
        H1 = cv2.normalize(H1, H1, 0, 1, cv2.NORM_MINMAX, -1)  # 对图片进行归一化处理

        cardImg = cv2.cvtColor(cardData, cv2.COLOR_BGR2GRAY)
        H2 = cv2.calcHist([cardImg], [0], None, [256], [0, 256])
        H2 = cv2.normalize(H2, H2, 0, 1, cv2.NORM_MINMAX, -1)

        # 利用compareHist（）进行比较相似度
        similarity = cv2.compareHist(H1, H2, 0)
        return np.mean(cardData) > 100 and similarity > 0.4

    def zombieRow(self, top) -> int:
        top -= FIRST_GRASS_OFFSET.y
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


def locateZombies(image, confidence=0.8) -> list[Point]:
    """
    获取所有僵尸的中心点
    :param image: 当前pvz图片
    :param confidence: 识别的置信度
    :return: List[Point]
    """
    # 调整图像大小以便输入模型
    img_detect = cv2.resize(image, (640, 640))

    # 使用模型进行预测
    # 注意: YOLOv8的predict方法不需要额外指定imgsz
    result = model.predict(source=img_detect, conf=confidence, save=False, verbose=False)
    boxes = result[0].boxes

    ret = []
    for box in boxes.xyxy:  # 使用xyxy格式来获取边界框
        x1, y1, x2, y2 = box.tolist()
        # x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        ret.append(Point((x1 + x2) // 2, (y1 + y2) // 2))
    return ret
