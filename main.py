import time
import cbjLibrary.log as log
import cbjLibrary.window as window
import screen
import pyautogui
from CONFIG import *

logger = log.initLogger(loggerName="pvz")


def chooseAndStart(sc: screen.PvzScreen):
    pyautogui.moveTo(*sc.baseLocate)  # 防止鼠标放到卡片上, 影响识别
    # 选植物
    image = sc.Shot()
    cards = [
        PLANT_SUNFLOWER,
        PLANT_REPEATER,
        PLANT_PUMPKIN,
        PLANT_SPIKE_WEED,
        PLANT_TORCH_WOOD,
        PLANT_TALL_NUT,
        PLANT_POTATO_MINE,
        PLANT_SQUASH,
    ]

    for card in cards:
        lo = screen.locateCenter(f"./data/{card}", image, confidence=0.95)
        pyautogui.leftClick(*(sc.baseLocate + lo))
    # 点击开始
    lo = pyautogui.locateCenterOnScreen("./data/start.jpg", confidence=0.7)
    pyautogui.moveTo(*lo)
    pyautogui.leftClick(*lo)


def growthStage(sc: screen.PvzScreen):
    sunFlowerCnt = 0  # 阳光花计数器, 到10结束当前阶段
    doubleShot = [0 for _ in range(5)]  # 双发射手数量
    tCnt = 0  # tick计时器, 用于不同间隔执行一些操作
    plants = [0, 0, 0, 0, 0]  # 每一行的植物数量
    while True:
        plant = -1  # 当前TICK需要种植的植物, 确保每一个TICK只能种一个植物, 防止重复种植导致阳光不够
        plantRow, plantCol = -1, -1
        time.sleep(TICK)
        tCnt += 1

        # 检查鼠标位置, 方便随时退出, 杜绝鼠标被完全控制的安全隐患
        if not sc.mouseInScreen():
            logger.error("mouse out of pvz, exit")
            exit(0)

        image = sc.Shot()

        # 捡阳光
        points = screen.locateAllCenter("./data/sun.jpg", image)
        for p in points:
            if p.y < screen.FIRST_GRASS_OFFSET.y - screen.GRASS_SIZE.y // 2:
                continue
            logger.debug("click sun")
            pyautogui.leftClick(*(sc.baseLocate + p))

        if tCnt != COMMON_TICKS:
            continue
        tCnt = 0

        points = screen.locateAllCenter("./data/zb3.jpg", image, confidence=ZOMBIE_CONFIDENCE)
        # 每行拥有僵尸的数量
        zombieCnt = [0, 0, 0, 0, 0]
        for p in points:
            row = sc.zombieRow(p.y)
            logger.info(str(row) + str(p))
            zombieCnt[row] += 1

        # 判断是否需要种植植物
        for row, cnt in enumerate(zombieCnt):
            if plants[row] >= cnt:
                continue
            if sunFlowerCnt < 10:
                # 种植土豆雷和窝瓜
                for i in [CARD_POTATO_MINE, CARD_SQUASH]:
                    # 优先种第四列, 如果两个僵尸则种第三列
                    col = 2 if plants[0] == 1 else 3
                    if sc.cardAvailable(image, i):
                        # 种植土豆雷/窝瓜
                        plant, plantRow, plantCol = i, row, col
                        plants[row] += 1
                        logger.info(f"种土豆雷/窝瓜 row={row}, col={col}")
                        break

        # 种向日葵
        if plant == -1 and sunFlowerCnt < 10 and sc.cardAvailable(image, CARD_SUNFLOWER):
            plant = CARD_SUNFLOWER
            plantCol, plantRow = divmod(sunFlowerCnt, 5)
            logger.info(f"plant a sunflower row={plantRow}, col={plantCol}")
            sunFlowerCnt += 1
            if sunFlowerCnt == 10:
                plants = zombieCnt

        # 种双发射手
        if plant == -1 and sunFlowerCnt == 10 and sc.cardAvailable(image, CARD_REPEATER):
            plant = CARD_REPEATER
            plantCol = 2
            for i in range(5):
                if zombieCnt[i] != 0 and plants[i] == 0 and doubleShot[i] == 0:
                    plantRow = i
                    break
            else:
                for i in range(5):
                    if doubleShot[i] == 0 and plants[i] == 0:
                        plantRow = i
                        break
                else:
                    plantRow = doubleShot.index(0)
            logger.info(f"plant a sunflower row={plantRow}, col={plantCol}")
            doubleShot[plantRow] = 1

        # 种植植物
        if plant != -1:
            pyautogui.leftClick(*(sc.baseLocate + sc.getCardCenter(plant)))
            pyautogui.leftClick(*(sc.baseLocate + sc.getGrass(plantRow, plantCol)))

        if sum(doubleShot) == 5:
            return


def plantStage(sc: screen.PvzScreen):
    plantCount = [0 for _ in range(10)]
    plantMax = [5 for _ in range(10)]
    plantMax[CARD_REPEATER] = 15  # 双发
    plantStart = {
        CARD_TALL_NUT: 7,
        CARD_SPIKE_WEED: 8,
        CARD_TORCH_WOOD: 6,
        CARD_REPEATER: 3,
        CARD_PUMPKIN: 6,
    }
    while True:
        plant = -1  # 当前TICK需要种植的植物, 确保每一个TICK只能种一个植物, 防止重复种植导致阳光不够
        plantRow, plantCol = -1, -1
        time.sleep(TICK)

        # 检查鼠标位置, 方便随时退出, 杜绝鼠标被完全控制的安全隐患
        if not sc.mouseInScreen():
            logger.error("mouse out of pvz, exit")
            exit(0)

        image = sc.Shot()
        if screen.locateCenter("./data/end.jpg", image) is not None:
            logger.error("a flag has ended")
            time.sleep(10)
            chooseAndStart(sc)
            time.sleep(5)
            continue

        # 捡阳光
        points = screen.locateAllCenter("./data/sun.jpg", image)
        for p in points:
            if p.y < screen.FIRST_GRASS_OFFSET.y - screen.GRASS_SIZE.y // 2:
                continue
            logger.debug("click sun")
            pyautogui.leftClick(*(sc.baseLocate + p))

        # 高坚果, 地刺, 火炬, 豌豆, 南瓜
        # TODO: 种植高坚果之后可以减少南瓜的种植, 尽快种植火炬
        # TODO: 实现阳光等待逻辑, 确保真正的植物优先级, 这里的种植顺序会受到植物本身所需阳光的影响
        for index in [CARD_TALL_NUT, CARD_SPIKE_WEED, CARD_TORCH_WOOD, CARD_REPEATER, CARD_PUMPKIN]:
            cnt = plantCount[index]
            if cnt < plantMax[index] and sc.cardAvailable(image, index):
                plant = index
                plantCol, plantRow = divmod(cnt, 5)
                if index == CARD_TALL_NUT:
                    plantRow = 4 - plantRow
                plantCol += plantStart[index]
                plantCount[index] += 1
                logger.info(f"plant a plant row={plantRow}, col={plantCol}")
                break

        # 种植植物
        if plant != -1:
            pyautogui.leftClick(*(sc.baseLocate + sc.getCardCenter(plant)))
            pyautogui.leftClick(*(sc.baseLocate + sc.getGrass(plantRow, plantCol)))

        if plantCount[CARD_REPEATER] == 15:
            logger.error("game end")
            return


def waitStage(sc: screen.PvzScreen):
    """
    种完植物的等待
    """
    while True:
        time.sleep(TICK)

        # 检查鼠标位置, 方便随时退出, 杜绝鼠标被完全控制的安全隐患
        if not sc.mouseInScreen():
            logger.error("mouse out of pvz, exit")
            exit(0)

        image = sc.Shot()
        if screen.locateCenter("./data/end.jpg", image) is not None:
            logger.error("a flag has ended")
            time.sleep(10)
            chooseAndStart(sc)
            time.sleep(5)
            continue

        # 捡阳光
        points = screen.locateAllCenter("./data/sun.jpg", image)
        for p in points:
            if p.y < screen.FIRST_GRASS_OFFSET.y - screen.GRASS_SIZE.y // 2:
                continue
            logger.debug("click sun")
            pyautogui.leftClick(*(sc.baseLocate + p))


def beat(sc: screen.PvzScreen):
    while True:
        time.sleep(0.3)

        # 检查鼠标位置, 方便随时退出, 杜绝鼠标被完全控制的安全隐患
        if not sc.mouseInScreen():
            logger.error("mouse out of pvz, exit")
            exit(0)
        image = sc.Shot()

        points = screen.locateAllCenter("./data/zb3.jpg", image, confidence=0.5)
        # 每行拥有僵尸的数量
        for p in points:
            pyautogui.leftClick(*(sc.baseLocate + p))


def easyDay():
    """
    白天简单模式
    """
    left, top, width, height = window.getWindowRect("MainWindow", "植物大战僵尸中文版")
    sc = screen.PvzScreen(left, top, width, height)
    # beat(sc)
    chooseAndStart(sc)
    time.sleep(2)  # 防止识别到外面的僵尸
    growthStage(sc)
    plantStage(sc)
    waitStage(sc)


if __name__ == '__main__':
    easyDay()
