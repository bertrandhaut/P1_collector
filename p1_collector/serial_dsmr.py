"""
Inspired from https://github.com/jvhaarst/DSMR-P1-telegram-reader/blob/master/telegram_from_serial.py
"""
import logging
import re
import crcmod
from dataclasses import dataclass
from typing import Union, Dict
from datetime import datetime

import serial

crc16 = crcmod.predefined.mkPredefinedCrcFun('crc16')

CODES = {
    '1-0:1.8.1': 'Meter Reading electricity delivered to client (Tariff 1) in kWh',
    '1-0:1.8.2': 'Meter Reading electricity delivered to client (Tariff 2) in kWh',
    '1-0:2.8.1': 'Meter Reading electricity delivered by client (Tariff 1) in kWh',
    '1-0:2.8.2': 'Meter Reading electricity delivered by client (Tariff 2) in kWh',
    '0-0:96.14.0': 'Tariff indicator electricity',
    '1-0:1.7.0': 'Actual electricity power delivered (+P) in kW',
    '1-0:2.7.0': 'Actual electricity power received (-P) in kW',
    '0-0:17.0.0': 'The actual threshold electricity in kW',
    '0-0:96.3.10': 'Switch position electricity',
    '0-0:96.7.21': 'Number of power failures in any phase',
    '0-0:96.7.9': 'Number of long power failures in any phase',
    '1-0:32.32.0': 'Number of voltage sags in phase L1',
    '1-0:52.32.0': 'Number of voltage sags in phase L2',
    '1-0:72:32.0': 'Number of voltage sags in phase L3',
    '1-0:32.36.0': 'Number of voltage swells in phase L1',
    '1-0:52.36.0': 'Number of voltage swells in phase L2',
    '1-0:72.36.0': 'Number of voltage swells in phase L3',
    '1-0:31.7.0': 'Instantaneous current L1 in A',
    '1-0:51.7.0': 'Instantaneous current L2 in A',
    '1-0:71.7.0': 'Instantaneous current L3 in A',
    '1-0:21.7.0': 'Instantaneous active power L1 (+P) in kW',
    '1-0:41.7.0': 'Instantaneous active power L2 (+P) in kW',
    '1-0:61.7.0': 'Instantaneous active power L3 (+P) in kW',
    '1-0:22.7.0': 'Instantaneous active power L1 (-P) in kW',
    '1-0:42.7.0': 'Instantaneous active power L2 (-P) in kW',
    '1-0:62.7.0': 'Instantaneous active power L3 (-P) in kW'
}

logger = logging.getLogger(__name__)


class InvalidChecksum(Exception):
    """Given checksum does not corresponds to computed checksum"""

@dataclass
class Measure:
    obis: str
    value: Union[float, int]
    unit: str
    comment: str

    def short_id(self):
        return self.obis.split(':')[1]

@dataclass
class Telegram:
    measures: Dict[str, Measure]
    timestamp: datetime


class SerialDSMR:

    def __init__(self):
        ser = serial.Serial()
        self.serial_conf = {'baudrate': 115200,
                            'bytesize': serial.EIGHTBITS,
                            'parity': serial.PARITY_NONE,
                            'stopbits': serial.STOPBITS_ONE,
                            'xonxoff': 1,
                            'rtscts': 0,
                            'timeout': 12,
                            'port': "/dev/ttyUSB0"}


    def parse_telegram(self, content: str) -> Telegram:
        measures = {}
        for obis in CODES.keys():
            m = re.search(f"{obis}\((.*)\)", content)
            if m is not None:
                s = m.group(1)

                # split in float/in + optionally unit
                if '*' in s:
                    value_s, unit = s.split('*')
                else:
                    value_s, unit = s, None
                if "." in value_s:
                    value = float(value_s)
                else:
                    value = int(value_s)

                measure = Measure(obis=obis,
                                     value=value,
                                     unit=unit,
                                     comment=CODES[obis])
                measures[measure.short_id()] = measure

        return Telegram(measures=measures,
                        timestamp=datetime.utcnow())

    def read_telegram(self) -> Telegram:
        with serial.Serial(**self.serial_conf) as ser:
            # read up to checksum
            telegram = ''
            checksum_found = False

            while not checksum_found:
                # Read a line
                telegram_line = ser.readline().decode('ascii')
                logger.debug(telegram_line.strip())

                telegram += telegram_line
                # Check if it matches the checksum line (! at start)
                if '!' in telegram_line:
                    checksum_found = True

        # extract relevant part
        content = re.match('.*(/.*!).*', telegram, re.DOTALL).group(1)
        logger.debug(content)
        checksum = int(re.match("!(.*)", telegram_line).group(1), 16)
        logger.debug(f'checksum: {checksum}')

        # validate checksum
        computed_checksum = crc16(content.encode('ascii'))
        if checksum != computed_checksum:
            raise InvalidChecksum()

        return self.parse_telegram(content)
