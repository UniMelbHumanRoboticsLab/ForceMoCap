from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from random import randint
pg.setConfigOptions(background='w')        # <── set theme once

import sys
import os
import numpy as np
import pandas as pd
from plot_force_ft import analyze_force
import matplotlib.pyplot as plt
np.set_printoptions(
    precision=4,
    linewidth=np.inf,   
    formatter={'float_kind': lambda x: f"{x:.4f}"}
)

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from force_tracking.firmware.python.pyRFT.rft_uart_server import *
from force_tracking.firmware.python.esp_serial.esp_serial_server import *

class Calibration_Widget(QtWidgets.QMainWindow):
    def __init__(self,hand,sensor,q1):
        super().__init__()

        # ➊ ---------- graphics layout with two rows -------------
        self.gw = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.gw)

        self.plot_top    = self._make_plot("RFT","F (N)")
        self.gw.nextRow()
        self.plot_bottom = self._make_plot("MLX", "B (mT)")

        # ➋ ---------- data buffers ------------------------------
        self.buffer_size = 300
        self.dim = 3
        self.clock = 0
        self.time_interval = 1/100
        # self.buffers = [
        #     [[randint(20, 40) for _ in range(self.buffer_size)] for _ in range(3)],  # subplot 0
        #     [[randint(20, 40) for _ in range(self.buffer_size)] for _ in range(3)]   # subplot 1
        # ]
        self.buffers = [
            [np.zeros(self.buffer_size)for _ in range(self.dim)],  # subplot 0
            [np.zeros(self.buffer_size)for _ in range(self.dim)]   # subplot 1
        ]

        # ➌ ---------- curves ------------------------------------
        pens    = ['r', 'g', 'b']
        names   = ['X', 'Y', 'Z']

        self.curves = []
        for plot in (self.plot_top, self.plot_bottom):
            csub = []
            for i in range(self.dim):
                csub.append(
                    plot.plot(self.buffers[0][i],
                              pen=pg.mkPen(pens[i], width=2),
                              name=names[i])
                )
            self.curves.append(csub)

        # ➍ ---------- init current calin config -------------------------------------
        self.q1 = q1
        self.q2 = 0
        self.force_data = []

        # ➍ ---------- init sensors -------------------------------------
        PORT_ESP = "COM9"
        self.esp = ESPSeriesServer(PORT_ESP)
        self.hand = hand
        self.sensor = sensor

        PORT_RFT = "COM7"
        self.rft = RFTSeriesServer(port = PORT_RFT)
        self.rft.init_and_collect()

        # ➍ ---------- key presses -------------------------------------
        # go to next angle
        QtWidgets.QShortcut("S", self, self.stop_cur_q2)

        # quit
        QtWidgets.QShortcut("Q", self, self.close)

        # ➍ ---------- timer -------------------------------------
        self.timer = QtCore.QTimer(self, interval=self.time_interval, timeout=self.update_plot)
        self.timer.start()
        self.start_time = time.perf_counter()
        self.q2_started = True

        QtWidgets.QShortcut("C", self, self.start_next_q2)

    def _make_plot(self, title,unit):
        plt = self.gw.addPlot()
        plt.setTitle(title, color='b', size='20pt')
        style = {"color": "red", "font-size": "16px"}
        plt.setLabel('left', unit, **style)
        plt.setLabel('bottom', 'Time (s)',**style)
        plt.addLegend(offset=(10, 10))
        plt.showGrid(x=True, y=True)
        # plt.setYRange(20, 40)
        return plt
    
    def start_next_q2(self):
        """To start the next q2"""
        if self.q2_started == False:
            plt.close("all")
            time.sleep(0.1)

            # change the q2 configuration
            self.q2 += 15
            print(f"\n================\nsensor_calib/{self.hand}/{self.sensor}/force_{self.q1}_{self.q2} started")

            # restart the sensors
            self.esp.restart()
            self.esp.wait_calibrate()
            self.rft.restart()
            self.rft.init_and_collect()

            # renew the data and time
            self.force_data = []
            self.start_time = time.perf_counter()
            self.q2_started = True

            self.timer.start()           # resume

    def stop_cur_q2(self):
        if self.q2_started == True:
            # save the collected data
            columns  =["t","Fx","Fy","Fz","Tx","Ty","Tz","Bx","By","Bz"]
            df = pd.DataFrame(self.force_data, columns=columns)
            df.to_csv(f"sensor_calib/data/{self.hand}/{self.sensor}/force_{self.q1}_{self.q2}.csv", index=False)
            print(f"sensor_calib/{self.hand}/{self.sensor}/force_{self.q1}_{self.q2} ended")

            analyze_force(df)
            self.q2_started = False
            self.timer.stop()

    def update_plot(self):
        try:
            rft_temp = self.rft.getTareFT()
            # print(rft_temp)
            # esp_temp = self.rft.getTareFT()
        except Exception as e:
            print(e)
        # rft_temp = self.esp.get_mlx_data()
        esp_temp = self.esp.get_mlx_data()
        self.force_data.append(np.concatenate((np.array(time.perf_counter()-self.start_time),rft_temp, esp_temp), axis=None))
        
        for s, buf_set in enumerate(self.buffers):
            for i in range(self.dim):
                if s == 0:
                    buf_set[i] = np.concatenate((buf_set[i][1:], [rft_temp[i]]))
                    # buf_set[i] = np.concatenate((buf_set[i][1:], [esp_temp[i]]))
                elif s == 1:
                    buf_set[i] = np.concatenate((buf_set[i][1:], [esp_temp[i]]))
                self.curves[s][i].setData(buf_set[i])

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = Calibration_Widget(hand="left",sensor="f1",q1=-60)
    win.resize(900, 700)
    win.show()
    pg.exec()           # pg.exec_() on PyQt ≤ 5.14