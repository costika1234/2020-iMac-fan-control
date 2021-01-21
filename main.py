import os
import re
import struct
import subprocess as sp
import time

from collections import deque
from pathlib import Path

# Constants.
PATH_TO_SMC = '/Applications/smcFanControl.app/Contents/Resources/smc'
MIN_FAN_SPEED_RPM = 1000
LOW_TEMP_THRESHOLD = 50.0
HIGH_TEMP_THRESHOLD = 65.0
FREQUENCY_PER_MIN = 30


class FanControl2020iMac():
    def __init__(self):
        self.has_default_settings = True
        self.no_cores = os.cpu_count() // 2
        self.history = deque(maxlen=FREQUENCY_PER_MIN)


    def _run_smc_read_cmd(self, key):
        args = [PATH_TO_SMC, '-r', '-k', key]
        command_output = sp.run(args, capture_output=True).stdout.decode('utf-8')

        return float(re.match(r'.+\]\s+(.+)\s\(', command_output).group(1))


    def _run_smc_write_cmd(self, key, value):
        sp.run([PATH_TO_SMC, '-k', key, '-w', value])


    def _get_cpu_core_temp(self, core_no):
        return self._run_smc_read_cmd(f'TC{core_no}c')


    def _get_cpu_temp(self):
        return sum([self._get_cpu_core_temp(i) for i in range(self.no_cores)]) / self.no_cores


    def _set_fan_speed(self, speed):
        self._run_smc_write_cmd('F0Md', '01')
        self._run_smc_write_cmd('F0Tg', bytearray(struct.pack('f', speed)).hex())


    def _set_default_fan_settings(self):
        self._run_smc_write_cmd('F0Md', '00')


    def _meets_default_settings_requirements(self, cpu_temp, avg_cpu_temp_last_min):
        # Apply default settings if:
        #   * there is a spike in the current CPU temperature;
        #   * or if the average CPU temperature over the last minute is greater than LOW_TEMP_THRESHOLD.
        return cpu_temp >= HIGH_TEMP_THRESHOLD or avg_cpu_temp_last_min >= LOW_TEMP_THRESHOLD


    def _adjust_fan_settings(self):
        # Get the current CPU temperature.
        cpu_temp = self._get_cpu_temp()

        # Calculate the average CPU temperature over the last minute.
        self.history.append(cpu_temp)
        avg_cpu_temp_last_min = sum(self.history) / len(self.history)

        if self._meets_default_settings_requirements(cpu_temp, avg_cpu_temp_last_min):
            if not self.has_default_settings:
               self._set_default_fan_settings()
               self.has_default_settings = True
        else:
            if self.has_default_settings:
                self._set_fan_speed(MIN_FAN_SPEED_RPM)
                self.has_default_settings = False


    def run(self):
        start_time = time.time()
        no_seconds = 60.0 / FREQUENCY_PER_MIN

        while True:
            self._adjust_fan_settings()
            time.sleep(no_seconds - ((time.time() - start_time) % no_seconds))


def main():
    fc = FanControl2020iMac()
    fc.run()


if __name__ == '__main__':
    main()
