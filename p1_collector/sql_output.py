import logging
from typing import Dict

import pymysql

from p1_collector.serial_dsmr import Telegram

logger = logging.getLogger(__name__)


class SQLOutput:

    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password = password
        self.db = db

    def add_measures(self, telegram: Telegram):
        logger.debug('Connect to database')
        con = pymysql.connect(host=self.host,
                              user=self.user,
                              password=self.password,
                              database=self.db)

        measures = telegram.measures
        timestamp = telegram.timestamp
        with con:
            cur = con.cursor()
            logger.debug('Executing SQL statement on database')

            sql = """INSERT INTO ENERGY (timestamp, `1.8.1`, `1.8.2`, `2.8.1`, `2.8.2`) VALUES (%s, %s, %s, %s, %s)"""
            cur.execute(sql, (timestamp,
                              measures['1.8.1'].value,
                              measures['1.8.2'].value,
                              measures['2.8.1'].value,
                              measures['2.8.2'].value))

            con.commit()
