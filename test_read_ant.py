# Проверка работоспособности антенны
from sllurp import llrp
from twisted.internet import reactor

from datetime import datetime
from log import logger

from config import TX_POWER, RFID_IP, NAME, WORK_ANT, ANTENNAS


def cb(tagReport):
    start = datetime.now()

    tags = tagReport.msgdict['RO_ACCESS_REPORT']['TagReportData']  # вытаскиваем данные от считывателя
    for d in tags:
        if d["AntennaID"][0] == WORK_ANT:
            logger.info(d)

    # тестируем скорость работы программы
    logger.info(f"Весь цикл занял: {datetime.now() - start}")

    # separator
    logger.info("*" * 40)
    logger.info("*" * 40)
    logger.info("*" * 40)


if __name__ == '__main__':
    factory = llrp.LLRPClientFactory(antennas=list(ANTENNAS.keys()), duration=1, tx_power={
        1: 1,
        2: TX_POWER,
        3: 1,
        4: 1,
    })
    factory.addTagReportCallback(cb)  # передача функции на исполнение
    reactor.connectTCP(RFID_IP, llrp.LLRP_PORT, factory, timeout=3)  # соединение
    print(f"****************** Starting work for '{NAME}' with IP: {RFID_IP} ******************")
    reactor.run()  # запуск

