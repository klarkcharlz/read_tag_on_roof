from sllurp import llrp
from twisted.internet import reactor
import psycopg2

from multiprocessing import Process
from time import sleep
import shelve

from config import ANTENNAS, RFID_IP, SCAN_TIME, WORK_ANT, CONNECT_DATA, NAME
from log import logger

reader = None
FILENAME = "tags"


def shutdown(factory):
    logger.info("ОСТАНАВЛИВАЮ")
    return factory.politeShutdown()


def get_ean13_checksum(tag):
    logger.info(f"Calculating checksum for {tag}")
    if tag.isnumeric():
        chet = 0
        nechet = 0
        index = 1
        for char in tag:
            if index % 2 == 0:
                chet += int(char)
            else:
                nechet += int(char)
            index += 1
        result_digit = chet * 3 + nechet
        result_digit = ((int(result_digit / 10) + 1) * 10 - result_digit) % 10
        return str(result_digit)
    else:
        return ""


def cb(tagReport):
    tags = tagReport.msgdict['RO_ACCESS_REPORT']['TagReportData']  # вытаскиваем данные от считывателя
    for d in tags:
        if 'EPC-96' in d:
            logger.info(f"Приняты данные: {d}.")
            ant = d["AntennaID"][0]
            if ant == WORK_ANT:
                tag = d['EPC-96'].decode('utf-8')
                rssi = d["PeakRSSI"][0]
                tag_with_ean13 = str(tag[2:].lstrip('0') + get_ean13_checksum(tag[2:].lstrip('0')))
                logger.info(f"Найдена метка: {tag_with_ean13}.")
                if tag_with_ean13:
                    tag = tag_with_ean13
                    with shelve.open(FILENAME) as f:
                        f[tag] = rssi
                    logger.info(f"Запись  метки {tag} в файл произвел.")


def read_tag(tx_power):
    try:
        factory = llrp.LLRPClientFactory(antennas=list(ANTENNAS.keys()), duration=1, tx_power=tx_power)
        factory.addTagReportCallback(cb)  # передача функции на исполнение
        reactor.connectTCP(RFID_IP, llrp.LLRP_PORT, factory, timeout=2)  # соединение
        reactor.addSystemEventTrigger('before', 'shutdown', shutdown, factory)
        logger.info(f"****************** Starting work {NAME} with IP: {RFID_IP} ******************")
        reactor.callLater(SCAN_TIME, shutdown, factory)
        reactor.run()
    except Exception as err:
        logger.error(err)
        raise ValueError


def insert_update_db(zone):
    with shelve.open(FILENAME) as f:
        tag_dict = {}
        for key in f:
            tag_dict[key] = f[key]
        logger.info(f"Зона {zone} - Метки {tag_dict}")
        logger.info(f"Увиденные метки и их сигнал:\n {tag_dict}")
        if not tag_dict:
            return "Метки не считалась."
    # определяем самую близкую метку
    items = list(tag_dict.items())
    items.sort(key=lambda tag: tag[1])
    logger.info(f"Все увиденные метки:\n{items}")
    tag = items[-1][0]
    logger.info(f"Самая близкая метка: {tag}")
    try:
        sql_conn = psycopg2.connect(**CONNECT_DATA)
        sql_cur = sql_conn.cursor()
        query = f"INSERT INTO test_landmark_tag(tag, zone) VALUES('{tag}', '{zone}');"
        logger.info("Добавляю.")
        sql_cur.execute(query)
        sql_conn.commit()
        sql_cur.close()
        sql_conn.close()
        logger.info("Запись в БД произведена.")
    except Exception as err:
        logger.error(err)
        return "Проблемы с подключением к базе данных."
    return f"\nЗапись метки {tag} для зоны {zone} успешно произведена."


def clear_tag_file():
    with shelve.open(FILENAME) as f:
        f.clear()
        logger.info("Произвел предварительную очистку файла-обменника")


def write(zone, tx_power):
    clear_tag_file()
    logger.info(f"Считывание метки для зоны {zone}.")
    global reader
    reader = Process(target=read_tag, args=(tx_power, ))
    logger.info("Начинаю чтение метки.")
    try:
        reader.start()
        sleep(10)
        reader.terminate()
    except ValueError:
        return "Проблемы с подключением к считывателю."
    logger.info("Чтение окончено")
    logger.info("Произвожу запись в БД.")
    status = insert_update_db(zone)
    clear_tag_file()
    return status
