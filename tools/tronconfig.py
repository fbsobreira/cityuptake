import configparser
import re

class TronConfigParser(configparser.RawConfigParser):
    def get(self, section, option):
        val = configparser.RawConfigParser.get(self, section, option)
        return val.replace('"', '')