#!/usr/bin/python3

# Copyright 2024 Husarion sp. z o.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# This file is deprecated but stays here for backward compatibility look here:
# https://github.com/husarion/rosbot-docker/blob/ros2/Dockerfile.hardware#L82

import argparse
import sys
import time

import gpiod
import sh


class FirmwareFlasher:
    def __init__(self, binary_file):
        self.binary_file = binary_file
        sys_arch = str(sh.uname("-m")).strip()

        self.max_approach_no = 3

        print(f"System architecture: {sys_arch}")

        if sys_arch == "armv7l":
            # Setups ThinkerBoard pins
            print("Device: ThinkerBoard\n")
            self.port = "/dev/ttyS1"
            gpio_chip = "/dev/gpiochip0"
            boot0_pin_no = 164
            reset_pin_no = 184

        elif sys_arch == "x86_64":
            # Setups UpBoard pins
            print("Device: UpBoard\n")
            self.port = "/dev/ttyS4"
            gpio_chip = "/dev/gpiochip4"
            boot0_pin_no = 17
            reset_pin_no = 18

        elif sys_arch == "aarch64":
            # Setups RPi pins
            print("Device: RPi\n")
            self.port = "/dev/ttyAMA0"
            gpio_chip = "/dev/gpiochip0"
            boot0_pin_no = 17
            reset_pin_no = 18

        else:
            print("Unknown device...")

        chip = gpiod.Chip(gpio_chip)
        self.boot0_pin = chip.get_line(boot0_pin_no)
        self.reset_pin = chip.get_line(reset_pin_no)

        self.boot0_pin.request("Flash", type=gpiod.LINE_REQ_DIR_OUT, default_val=False)
        self.reset_pin.request("Flash", type=gpiod.LINE_REQ_DIR_OUT, default_val=False)

    def enter_bootloader_mode(self):
        self.boot0_pin.set_value(1)
        self.reset_pin.set_value(1)
        time.sleep(0.2)
        self.reset_pin.set_value(0)
        time.sleep(0.2)

    def exit_bootloader_mode(self):
        self.boot0_pin.set_value(0)
        self.reset_pin.set_value(1)
        time.sleep(0.2)
        self.reset_pin.set_value(0)
        time.sleep(0.2)

    def try_flash_operation(self, operation_name, flash_args):
        self.enter_bootloader_mode()

        print(f"{operation_name} operation started.")
        for i in range(self.max_approach_no):
            try:
                if operation_name == "Flashing":
                    sh.stm32flash(self.port, *flash_args, _out=sys.stdout)
                    print("Success! The robot firmware has been uploaded.")
                else:
                    sh.stm32flash(self.port, *flash_args)
                break
            except Exception as e:
                stderr = e.stderr.decode('utf-8')
                if stderr:
                    print(f"[ERROR] [{operation_name}]: \n\t{stderr}.")
                else:
                    break
            time.sleep(0.2)  # Delay between attempts

        self.exit_bootloader_mode()

    def flash_firmware(self):
        # Disable the flash write-protection
        self.try_flash_operation("Write-UnProtection", ["-u"])

        # Disable the flash read-protection
        self.try_flash_operation("Read-UnProtection", ["-k"])

        # Flashing the firmware
        flash_args = ["-v", "-w", self.binary_file, "-b", "115200"]
        self.try_flash_operation("Flashing", flash_args)


def main():
    parser = argparse.ArgumentParser(
        description="Flashing the firmware on STM32 microcontroller in ROSbot"
    )

    parser.add_argument(
        "-f",
        "--file",
        nargs="?",
        default="/root/firmware.bin",
        help="Path to a firmware file. Default = /root/firmware.bin",
    )

    binary_file = parser.parse_args().file

    flasher = FirmwareFlasher(binary_file)
    flasher.flash_firmware()


if __name__ == "__main__":
    main()
