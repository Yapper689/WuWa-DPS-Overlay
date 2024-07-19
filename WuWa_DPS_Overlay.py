from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor
from datetime import datetime
import threading
import time as timesleep
import os
import sys

class DPSOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.entities = {}
        self.highest_dps = 0
        self.last_damage_time = None
        self.reset_period = 5  # seconds

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateDPS)
        self.timer.start(200)  # Update every 200ms

        threading.Thread(target=self.read_log_file, daemon=True).start()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 400, 200)

        self.layout = QVBoxLayout()
        
        self.dps_label = QLabel('DPS: 0', self)
        self.highest_dps_label = QLabel('Highest DPS: 0', self)
        
        font_size = '32px'
        self.dps_label.setStyleSheet(f"QLabel {{ color: white; font-size: {font_size}; text-align: left; }}")
        self.highest_dps_label.setStyleSheet(f"QLabel {{ color: white; font-size: {font_size}; text-align: left; }}")
        
        self.layout.addWidget(self.dps_label)
        self.layout.addWidget(self.highest_dps_label)
        self.setLayout(self.layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(0, 0, 0, 127))
        painter.drawRect(self.rect())

    def updateDPS(self):
        current_time = datetime.now()
        
        if self.last_damage_time and (current_time - self.last_damage_time).seconds > self.reset_period:
            current_dps = 0
        else:
            dps_10s_values = [entity['dps10s'] for entity in self.entities.values() if 'dps10s' in entity]
            current_dps = sum(dps_10s_values) if dps_10s_values else 0

        
        dps_text = f"DPS: {current_dps:.2f}"
        highest_dps_text = f"Highest DPS: {self.highest_dps:.2f}"
        
        self.dps_label.setText(dps_text)
        self.highest_dps_label.setText(highest_dps_text)

    def read_log_file(self):
        while True:
            entities = {}
            logsFile = None
            lines = None
            try:
                logsFile = open('C:\\Wuthering Waves\\Wuthering Waves Game\\Client\\Saved\\Logs\\Client.log', 'r', encoding="utf-8")
                lines = logsFile.readlines()
            except:
                print('Error reading log file')
                if logsFile:
                    logsFile.close()
                timesleep.sleep(0.2)
                continue

            current_time = datetime.now()

            for i in range(len(lines)-1,-1,-1):
                if 'LifeValue' in lines[i]:
                    try:
                        past_hp = float(lines[i].partition('LifeValue: ')[2].partition(']')[0])
                        entity_id = lines[i].partition('[EntityId:')[2].partition(':')[0]

                        log_time = datetime.strptime(lines[i][1:24], "%Y.%m.%d-%H.%M.%S:%f")

                        if entity_id not in entities:
                            entities[entity_id] = {'hp': past_hp, 'name': lines[i].partition('Monster:BP_')[2].partition('_')[0], 'last_combat_time': log_time}

                        if (current_time - log_time).seconds < 10 and (current_time - log_time).seconds > 0:
                            dps_10s = (past_hp - entities[entity_id]['hp']) / (current_time - log_time).seconds
                            entities[entity_id]['dps10s'] = dps_10s
                            self.highest_dps = max(self.highest_dps, dps_10s)
                            entities[entity_id]['hp'] = past_hp
                            entities[entity_id]['last_combat_time'] = current_time
                            self.last_damage_time = current_time
                    except ValueError:
                        continue

            self.entities = entities

            timesleep.sleep(0.2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = DPSOverlay()
    overlay.show()
    sys.exit(app.exec_())