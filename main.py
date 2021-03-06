# -*- coding: utf-8 -*-
"""
Created on 2021-11-13

@author: rfwebster
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest
from ui.beamshower_ui import Ui_MainWindow
import math

_status = 0  # online
try:
    from PyJEM import detector, TEM3
    TEM3.connect()
except(ImportError):
    from PyJEM.offline import detector, TEM3
    _status = 1  # offline


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.startButton.clicked.connect(self.go)

        self.lens = TEM3.Lens3()
        self.deflector = TEM3.Def3()
        self.eos = TEM3.EOS3()
        self.det = TEM3.Detector3()

        self.cl1 = 1000 # change these to the values required for beam shower
        self.cl2 = 1000
        self.cl3 = 1000
        self.bk_cl1 = 0
        self.bk_cl2 = 0
        self.bk_cl3 = 0
        self.probe_size = self.eos.GetSpotSize()

        # determine inserted detectors:
        self.inserted_detectors = []
        for d in detector.get_attached_detector():
            if self.det.GetPosition(d) == 1:
                self.inserted_detectors.append(d)
        print("Inserted Detectors: {}".format(self.inserted_detectors))

        self.time = 15*60*1000
        self.time_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.countdown)

    def countdown(self):
        """
        counts down from the self.time and updates the progress bar
        when finihed resets the TEM condtions
        :return:
        """
        self.time_count += 1000
        value = int(self.time_count/self.time * 100)

        time_remaining = int(self.time-self.time_count)
        mins = math.floor((time_remaining / 1000) / 60)
        secs = int((time_remaining / 1000) % 60)
        if value < 100:
            self.progressBar.setValue(value)
            self.progressBar.setFormat("Time Remaining: {:2} : {:2}".format(mins, secs))
        else:
            self.progressBar.setValue(100)
            self.timer.stop()
            # reset TEM
            self.reset()
            self.startButton.setText("Start Beam Shower")
            self.progressBar.setFormat("")
            self.startButton.setEnabled(True)

    def go(self):
        """
        Runs the program
            - Saves the current conditions
            - Blanks the beam
            - Sets the probe size to 5/4
            - Sets the CL lens values for beam shower
            - Removes detectors
            - Blanks beam under the sample (using deflectors)
            - Unblanks B
            eam
        :return:
        """
        self.startButton.setDisabled(True)
        self.save_cl_values()
        self.blank_beam(True)
        self.startButton.setText("Blanking Beam")
        QTest.qWait(1 * 1000)
        self.get_conditions()
        self.startButton.setText("Setting Lenses")
        QTest.qWait(2 * 1000)
        self.eos.SelectSpotSize(5)  # set spot size 5
        self.set_cl_values()
        self.startButton.setText("Removing Detectors")
        self.remove_detectors()
        QTest.qWait(10 * 1000)
        self.blank_beam(False)
        self.startButton.setText("Running Beam Shower")

        print(self.time)
        # wait for the time and do the progress bar and label
        self.timer.start(1000)

    def get_conditions(self):
        """
        Gets conditions from the UI
        TODO: make relative change
        :return:
        """
        self.time = int(self.time_spinBox.text())*60*1000
        self.cl1 = int(self.CL1_spinBox.text(),16)
        print(self.cl1)
        self.cl2 = int(self.CL2_spinBox.text(),16)
        self.cl3 = int(self.CL3_spinBox.text(),16)

        return

    def save_cl_values(self):
        """
        Saves the orignal CL values to a file as a backup
        :return:
        """
        self.bk_cl1 = self.lens.GetCL1()
        self.bk_cl2 = self.lens.GetCL2()
        self.bk_cl3 = self.lens.GetCL3()
        txt = "cl1:{}\n" \
              "cl2:{}\n" \
              "cl3:{}".format(self.bk_cl1, self.bk_cl2, self.bk_cl3)
        print(txt)
        with open("./cl-values.txt", "w") as f:
            f.write(txt)

    def blank_beam(self, blank):
        """
        Blanks Beam if input is True
        :param blank:
        :return:
        """
        if blank is True:
            # blank beam
            self.deflector.SetBeamBlank(1)
        else:
            # un-blank beam
            self.deflector.SetBeamBlank(0)

    def set_cl_values(self):
        """
        Sets the condensor lens values to those used for the beam shower
        TODO - work for more than one spot size
        TODO: make relative change - need to find out what the relative values are
        :return:
        """
        self.lens.SetFLCAbs(0, self.cl1)
        self.lens.SetFLCAbs(1, self.cl2)
        self.lens.SetFLCAbs(2, self.cl3)

    def remove_detectors(self):
        """
        Removes all detectors
        :return:
        """
        for d in self.inserted_detectors:
            self.det.SetPosition(d, 1)
        self.det.SetScreen(0)

    def insert_detectors(self):
        """
        Inserts all detectors
        :return:
        """
        for d in self.inserted_detectors:
            self.det.SetPosition(d, 1)
        self.det.SetScreen(2)

    def reset(self):
        """
        Resets all deflectors, apertutres and detectors to orignal values
        :return:
        """
        self.startButton.setText("Resetting Lenses")
        self.lens.SetFLCAbs(0, self.bk_cl1) # TODO:  better way to reset Free Lens Control?
        self.lens.SetFLCAbs(1, self.bk_cl2)
        self.lens.SetFLCAbs(2, self.bk_cl3)
        self.eos.SelectSpotSize(self.probe_size)
        QTest.qWait(2 * 1000)
        self.startButton.setText("Inserting Detectors")
        self.insert_detectors()
        QTest.qWait(10 * 1000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
