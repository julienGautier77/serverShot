# -*- coding: utf-8 -*-
#
# This file is part of the NIUSB6009 project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

""" NI USB 6009

"""

__all__ = ["NIUSB6009", "main"]

# PyTango imports
import PyTango
from PyTango import DebugIt
from PyTango.server import run
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command
from PyTango.server import class_property, device_property
from PyTango import AttrQuality, AttrWriteType, DispLevel, DevState

# from ArchivingDevice import ArchivingDevice
# Additional import
# PROTECTED REGION ID(NIUSB6009.additionnal_import) ENABLED START #

import nidaqmx
from dataclasses import dataclass
import threading
import time
from ..ArchivingDevice.ArchivingDevice import ArchivingDevice
from ..NIUSBFlipper.NIUSBFlipper import NIUSBFlipper

# PROTECTED REGION END #    //  NIUSB6009.additionnal_import


class NIUSB6009(ArchivingDevice):
    """ """

    __metaclass__ = DeviceMeta
    # PROTECTED REGION ID(NIUSB6009.class_variable) ENABLED START #

    @dataclass
    class DigitalChannel:
        port: int = 0
        channel: int = 0
        device_name: str = ""
        output_value: bool = False
        _is_output: bool = False

        @property
        def is_output(self):
            return self._is_output

        @is_output.setter
        def is_output(self, value):
            self._is_output = value

        @property
        def daqmx_name(self):
            return f"{self.device_name}/port{self.port}/line{self.channel}"

        @property
        def short_name(self):
            return f"P{self.port}{self.channel}"

        @property
        def state(self):
            if not self.is_output:
                with nidaqmx.Task() as task:
                    task.di_channels.add_di_chan(self.daqmx_name)
                    result = task.read()
                    print(self.daqmx_name, result)
                    value = result
            else:
                value = self.output_value
            return value

        @state.setter
        def state(self, value):
            print(self.daqmx_name, self.is_output)
            if self.is_output:
                with nidaqmx.Task() as task:
                    task.do_channels.add_do_chan(self.daqmx_name)
                    val = task.write(value)

    class CounterThread(threading.Thread):
        def __init__(self, trigger_callback, refresh_rate=100, device_name="Dev1"):
            super().__init__()
            self.counter = 0
            self.trigger_callback = trigger_callback
            self.refresh_rate = refresh_rate
            self.device_name = device_name

        def run(self, *args, **kwargs):
            self.counter_thread()

        def counter_thread(self):
            with nidaqmx.Task() as task:
                task.ci_channels.add_ci_count_edges_chan(
                    f"{self.device_name}/ctr0", edge=nidaqmx.constants.Edge.FALLING
                )
                task.start()
                old_value = -1
                trigger_time_last = time.time()
                while True:
                    val = task.read()
                    if not old_value == val:
                        old_value = val
                        trigger_time_current = time.time()
                        if trigger_time_current > trigger_time_last + 0.2:
                            trigger_time_last = trigger_time_current
                            self.trigger_callback()
                    time.sleep(1 / self.refresh_rate)

    def trigger_callback(self):
        self._attr_Counter += 1
        self.push_data_ready_event("Counter", self._attr_Counter)

    # PROTECTED REGION END #    //  NIUSB6009.class_variable
    # ----------------
    # Class Properties
    # ----------------

    # -----------------
    # Device Properties
    # -----------------

    DeviceName = device_property(dtype="str", default_value="Dev1")
    CounterRefreshRate = device_property(dtype="double", default_value=100)
    # ----------
    # Attributes
    # ----------

    Counter = attribute(
        dtype="uint",
        access=AttrWriteType.READ_WRITE,
    )
    P00 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P01 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P02 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P03 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P04 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P05 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P06 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P07 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P10 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P11 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P12 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P13 = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P00IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P01IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P02IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P03IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P04IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P05IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P06IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P07IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P10IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P11IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P12IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    P13IsOutput = attribute(
        dtype="bool",
        access=AttrWriteType.READ_WRITE,
    )
    # ---------------
    # General methods
    # ---------------

    def init_device(self):
        ArchivingDevice.init_device(self)
        self.Counter.set_data_ready_event(True)
        # PROTECTED REGION ID(NIUSB6009.init_device) ENABLED START #
        print("init")
        self.digital_channels = {
            "P00": self.DigitalChannel(0, 0, self.DeviceName),
            "P01": self.DigitalChannel(0, 1, self.DeviceName),
            "P02": self.DigitalChannel(0, 2, self.DeviceName),
            "P03": self.DigitalChannel(0, 3, self.DeviceName),
            "P04": self.DigitalChannel(0, 4, self.DeviceName),
            "P05": self.DigitalChannel(0, 5, self.DeviceName),
            "P06": self.DigitalChannel(0, 6, self.DeviceName),
            "P07": self.DigitalChannel(0, 7, self.DeviceName),
            "P10": self.DigitalChannel(1, 0, self.DeviceName),
            "P11": self.DigitalChannel(1, 1, self.DeviceName),
            "P12": self.DigitalChannel(1, 2, self.DeviceName),
            "P13": self.DigitalChannel(2, 6, self.DeviceName),
        }

        # Set up the trigger counter

        self._attr_Counter = 0

        self.counter_thread = self.CounterThread(
            self.trigger_callback, self.CounterRefreshRate, self.DeviceName
        )
        self.counter_thread.start()

        # PROTECTED REGION END #    //  NIUSB6009.init_device

    def always_executed_hook(self):
        # PROTECTED REGION ID(NIUSB6009.always_executed_hook) ENABLED START #
        pass
        # PROTECTED REGION END #    //  NIUSB6009.always_executed_hook

    def delete_device(self):
        # PROTECTED REGION ID(NIUSB6009.delete_device) ENABLED START #
        self.counter_task.cancel()
        # PROTECTED REGION END #    //  NIUSB6009.delete_device

    # ------------------
    # Attributes methods
    # ------------------

    def read_Counter(self):
        # PROTECTED REGION ID(NIUSB6009.Counter_read) ENABLED START #
        return self._attr_Counter
        # PROTECTED REGION END #    //  NIUSB6009.Counter_read

    def write_Counter(self, value):
        # PROTECTED REGION ID(NIUSB6009.Counter_write) ENABLED START #
        self._attr_Counter = value
        # PROTECTED REGION END #    //  NIUSB6009.Counter_write

    def read_P00(self):
        # PROTECTED REGION ID(NIUSB6009.P00_read) ENABLED START #
        return self.digital_channels["P00"].state
        # PROTECTED REGION END #    //  NIUSB6009.P00_read

    def write_P00(self, value):
        # PROTECTED REGION ID(NIUSB6009.P00_write) ENABLED START #
        self.digital_channels["P00"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P00_write

    def read_P01(self):
        # PROTECTED REGION ID(NIUSB6009.P01_read) ENABLED START #
        return self.digital_channels["P01"].state
        # PROTECTED REGION END #    //  NIUSB6009.P01_read

    def write_P01(self, value):
        # PROTECTED REGION ID(NIUSB6009.P01_write) ENABLED START #
        self.digital_channels["P01"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P01_write

    def read_P02(self):
        # PROTECTED REGION ID(NIUSB6009.P02_read) ENABLED START #
        return self.digital_channels["P02"].state
        # PROTECTED REGION END #    //  NIUSB6009.P02_read

    def write_P02(self, value):
        # PROTECTED REGION ID(NIUSB6009.P02_write) ENABLED START #
        self.digital_channels["P02"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P02_write

    def read_P03(self):
        # PROTECTED REGION ID(NIUSB6009.P03_read) ENABLED START #
        return self.digital_channels["P03"].state
        # PROTECTED REGION END #    //  NIUSB6009.P03_read

    def write_P03(self, value):
        # PROTECTED REGION ID(NIUSB6009.P03_write) ENABLED START #
        self.digital_channels["P03"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P03_write

    def read_P04(self):
        # PROTECTED REGION ID(NIUSB6009.P04_read) ENABLED START #
        return self.digital_channels["P04"].state
        # PROTECTED REGION END #    //  NIUSB6009.P04_read

    def write_P04(self, value):
        # PROTECTED REGION ID(NIUSB6009.P04_write) ENABLED START #
        self.digital_channels["P04"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P04_write

    def read_P05(self):
        # PROTECTED REGION ID(NIUSB6009.P05_read) ENABLED START #
        return self.digital_channels["P05"].state
        # PROTECTED REGION END #    //  NIUSB6009.P05_read

    def write_P05(self, value):
        # PROTECTED REGION ID(NIUSB6009.P05_write) ENABLED START #
        self.digital_channels["P05"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P05_write

    def read_P06(self):
        # PROTECTED REGION ID(NIUSB6009.P06_read) ENABLED START #
        return self.digital_channels["P06"].state
        # PROTECTED REGION END #    //  NIUSB6009.P06_read

    def write_P06(self, value):
        # PROTECTED REGION ID(NIUSB6009.P06_write) ENABLED START #
        self.digital_channels["P06"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P06_write

    def read_P07(self):
        # PROTECTED REGION ID(NIUSB6009.P07_read) ENABLED START #
        return self.digital_channels["P07"].state
        # PROTECTED REGION END #    //  NIUSB6009.P07_read

    def write_P07(self, value):
        # PROTECTED REGION ID(NIUSB6009.P07_write) ENABLED START #
        self.digital_channels["P07"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P07_write

    def read_P10(self):
        # PROTECTED REGION ID(NIUSB6009.P10_read) ENABLED START #
        return self.digital_channels["P10"].state
        # PROTECTED REGION END #    //  NIUSB6009.P10_read

    def write_P10(self, value):
        # PROTECTED REGION ID(NIUSB6009.P10_write) ENABLED START #
        self.digital_channels["P10"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P10_write

    def read_P11(self):
        # PROTECTED REGION ID(NIUSB6009.P11_read) ENABLED START #
        return self.digital_channels["P11"].state
        # PROTECTED REGION END #    //  NIUSB6009.P11_read

    def write_P11(self, value):
        # PROTECTED REGION ID(NIUSB6009.P11_write) ENABLED START #
        self.digital_channels["P11"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P11_write

    def read_P12(self):
        # PROTECTED REGION ID(NIUSB6009.P12_read) ENABLED START #
        return self.digital_channels["P12"].state
        # PROTECTED REGION END #    //  NIUSB6009.P12_read

    def write_P12(self, value):
        # PROTECTED REGION ID(NIUSB6009.P12_write) ENABLED START #
        self.digital_channels["P12"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P12_write

    def read_P13(self):
        # PROTECTED REGION ID(NIUSB6009.P13_read) ENABLED START #
        return self.digital_channels["P13"].state
        # PROTECTED REGION END #    //  NIUSB6009.P13_read

    def write_P13(self, value):
        # PROTECTED REGION ID(NIUSB6009.P13_write) ENABLED START #
        self.digital_channels["P13"].state = value
        # PROTECTED REGION END #    //  NIUSB6009.P13_write

    def read_P00IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P00IsOutput_read) ENABLED START #
        return self.digital_channels["P00"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P00IsOutput_read

    def write_P00IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P00IsOutput_write) ENABLED START #
        self.digital_channels["P00"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P00IsOutput_write

    def read_P01IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P01IsOutput_read) ENABLED START #
        return self.digital_channels["P01"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P01IsOutput_read

    def write_P01IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P01IsOutput_write) ENABLED START #
        self.digital_channels["P01"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P01IsOutput_write

    def read_P02IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P02IsOutput_read) ENABLED START #
        return self.digital_channels["P02"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P02IsOutput_read

    def write_P02IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P02IsOutput_write) ENABLED START #
        self.digital_channels["P02"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P02IsOutput_write

    def read_P03IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P03IsOutput_read) ENABLED START #
        return self.digital_channels["P03"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P03IsOutput_read

    def write_P03IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P03IsOutput_write) ENABLED START #
        self.digital_channels["P03"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P03IsOutput_write

    def read_P04IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P04IsOutput_read) ENABLED START #
        return self.digital_channels["P04"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P04IsOutput_read

    def write_P04IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P04IsOutput_write) ENABLED START #
        self.digital_channels["P04"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P04IsOutput_write

    def read_P05IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P05IsOutput_read) ENABLED START #
        return self.digital_channels["P05"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P05IsOutput_read

    def write_P05IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P05IsOutput_write) ENABLED START #
        self.digital_channels["P05"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P05IsOutput_write

    def read_P06IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P06IsOutput_read) ENABLED START #
        return self.digital_channels["P06"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P06IsOutput_read

    def write_P06IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P06IsOutput_write) ENABLED START #
        self.digital_channels["P06"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P06IsOutput_write

    def read_P07IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P07IsOutput_read) ENABLED START #
        return self.digital_channels["P07"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P07IsOutput_read

    def write_P07IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P07IsOutput_write) ENABLED START #
        self.digital_channels["P07"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P07IsOutput_write

    def read_P10IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P10IsOutput_read) ENABLED START #
        return self.digital_channels["P10"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P10IsOutput_read

    def write_P10IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P10IsOutput_write) ENABLED START #
        self.digital_channels["P10"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P10IsOutput_write

    def read_P11IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P11IsOutput_read) ENABLED START #
        return self.digital_channels["P11"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P11IsOutput_read

    def write_P11IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P11IsOutput_write) ENABLED START #
        self.digital_channels["P11"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P11IsOutput_write

    def read_P12IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P12IsOutput_read) ENABLED START #
        return self.digital_channels["P12"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P12IsOutput_read

    def write_P12IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P12IsOutput_write) ENABLED START #
        self.digital_channels["P12"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P12IsOutput_write

    def read_P13IsOutput(self):
        # PROTECTED REGION ID(NIUSB6009.P13IsOutput_read) ENABLED START #
        return self.digital_channels["P13"].is_output
        # PROTECTED REGION END #    //  NIUSB6009.P13IsOutput_read

    def write_P13IsOutput(self, value):
        # PROTECTED REGION ID(NIUSB6009.P13IsOutput_write) ENABLED START #
        self.digital_channels["P13"].is_output = value
        # PROTECTED REGION END #    //  NIUSB6009.P13IsOutput_write

    # --------
    # Commands
    # --------


# ----------
# Run server
# ----------


def main(args=None, **kwargs):
    # PROTECTED REGION ID(NIUSB6009.main) ENABLED START #
    from PyTango.server import run

    return run(
        (
            NIUSB6009,
            NIUSBFlipper,
        ),
        args=args,
        **kwargs,
    )
    # PROTECTED REGION END #    //  NIUSB6009.main


if __name__ == "__main__":
    main()
