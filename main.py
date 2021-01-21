import re
import subprocess as sp
import struct
import time

from pathlib import Path

# Constants.
PATH_TO_SMC = '/Applications/smcFanControl.app/Contents/Resources/smc'
MIN_FAN_SPEED_RPM = 1000
LOW_TEMP_THRESHOLD = 50.0
HIGH_TEMP_THRESHOLD = 65.0
FREQUENCY_PER_MIN = 30
NO_CORES = 8


class FanControl2020iMac():
    def __init__(self):
        self.has_default_settings = True


    def __run_smc_read_cmd(self, key):
        args = [PATH_TO_SMC, '-r', '-k', key]
        command_output = sp.run(args, capture_output=True).stdout.decode('utf-8')

        return float(re.match(r'.+\]\s+(.+)\s\(', command_output).group(1))


    def __run_smc_write_cmd(self, key, value):
        sp.run([PATH_TO_SMC, '-k', key, '-w', value])


    def __get_cpu_core_temp(self, core_no):
        return self.__run_smc_read_cmd(f'TC{core_no}c')


    def __get_avg_cpu_temp(self):
        return sum([self.__get_cpu_core_temp(i) for i in range(NO_CORES)]) / NO_CORES


    def __set_fan_speed(self, speed):
        self.__run_smc_write_cmd('F0Md', '01')
        self.__run_smc_write_cmd('F0Tg', bytearray(struct.pack('f', speed)).hex())


    def __set_default_fan_settings(self):
        self.__run_smc_write_cmd('F0Md', '00')


    def __meets_default_settings_requirements(self):
        avg_cpu_temp = self.__get_avg_cpu_temp()
        print(avg_cpu_temp)

        return avg_cpu_temp >= HIGH_TEMP_THRESHOLD or \
               (self.has_default_settings and avg_cpu_temp >= LOW_TEMP_THRESHOLD)


    def __adjust_fan_settings(self):
        if self.__meets_default_settings_requirements():
            self.has_default_settings = True
            self.__set_default_fan_settings()
        else:
            self.has_default_settings = False
            self.__set_fan_speed(MIN_FAN_SPEED_RPM)


    def run(self):
        start_time = time.time()
        no_seconds = 60.0 / FREQUENCY_PER_MIN

        while True:
            self.__adjust_fan_settings()
            time.sleep(no_seconds - ((time.time() - start_time) % no_seconds))


def main():
    fc = FanControl2020iMac()
    fc.run()


if __name__ == '__main__':
    main()
