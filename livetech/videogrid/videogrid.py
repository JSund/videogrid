#!/usr/bin/env python

from __future__ import division
import sys
import math
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.phonon import Phonon
import redis
import livetech.prop.prop as prop

class TeamVideoPlayer(QFrame):
    def __init__(self, team_id, source, inactive_color, active_color, parent = None):
        QFrame.__init__(self, parent)

        self.team_id = team_id
        self.source = source
        self.inactive_color = inactive_color
        self.active_color = active_color
        self.player = Phonon.VideoPlayer()
        self.player.audioOutput().setVolume(0.0)
        self.player.audioOutput().setMuted(True)

        layout = QGridLayout(self)
        layout.addWidget(self.player, 0, 1)

    def show(self):
        self.player.play(self.source)
        self.player.audioOutput().setVolume(0.0)
        self.player.audioOutput().setMuted(True)

        self.setLineWidth(10)
        self.setFrameStyle(QFrame.Panel)
        self.setInactive()

        team_id_text = QLabel(str(self.team_id), self.player)
	team_id_text.setStyleSheet("QLabel { background-color: black; color: white; }")
        font = QFont()
        font.setPointSize(32)
        font.setBold(True)
        team_id_text.setFont(font)

        QFrame.show(self)

    def setActive(self):
        self.setPalette(self.active_color)

    def setInactive(self):
        self.setPalette(self.inactive_color)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print "Emitting selected team (by click): ", self.team_id
            self.emit(SIGNAL("select_team(int, bool)"), self.team_id, True)

class VideoGrid(QWidget):
    def __init__(self, mixer, parent = None):
        QWidget.__init__(self, parent)
        self.mixer=mixer

        self.key_presses = 0
        self.layout = QGridLayout(self)

    def keyReleaseEvent(self, event):
        if Qt.Key_0 <= event.key() <= Qt.Key_9:
            self.key_presses = self.key_presses*10 + event.key() - Qt.Key_0
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.key_presses > 0:
                print "Emitting selected team (by keyboard): ", self.key_presses
                for player in self.players.itervalues():
                    player.emit(SIGNAL("select_team(int, bool)"), self.key_presses, True)
                    break
                self.key_presses = 0
                
        elif event.key() == Qt.Key_Backspace:
            self.key_presses //= 10
        elif event.key() == Qt.Key_Escape:
            self.key_presses = 0
        elif event.key() == Qt.Key_Q:
            sys.exit(0)
        elif event.key() == Qt.Key_S:
            print "Checking state of all players."
            stopped_players = False
            for player in self.players.itervalues():
                player.player.play()
                if not player.player.isPlaying():
                    stopped_players = True
                    print "Restarting player ", player.team_id
                    player.player.play(self.teams_prop.get(str(player.team_id) + ".path").getValue())
            if not stopped_players:
                print "All players playing."
        elif event.key() == Qt.Key_F or event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            QWidget.keyReleaseEvent(self, event)

    def addTeams(self, teams, teams_prop):
        self.teams_propj = teams_prop
        inactive_color = QPalette()
        inactive_color.setColor(QPalette.WindowText, Qt.transparent)
        active_color = QPalette()
        active_color.setColor(QPalette.WindowText, Qt.red)

        cols = int(math.ceil(math.sqrt(len(teams))))
        rows = int(math.ceil(len(teams) / cols))
        self.players = {}
        for i in range(len(teams)):
            team = teams[i]
            path = teams_prop.get(str(team) + ".path").getValue()
            source = Phonon.MediaSource(QUrl(path))
            player = TeamVideoPlayer(team, source, inactive_color, active_color, self)
            QObject.connect(player, SIGNAL("select_team(int, bool)"), self.mixer.selectTeam, Qt.QueuedConnection)
            self.players[team] = player
            self.layout.addWidget(self.players[team], i // cols, i % cols)

        for i in range(cols):
            self.layout.setColumnStretch(i, 1)
        for i in range(rows):
            self.layout.setRowStretch(i, 1)

        for player in self.players.values():
            player.show()

        self.showNormal()
        self.resize(1024, 768)
        return self.players

class GridMixer(QObject):
    def __init__(self, hostname, preview_prop, teams_prop, selected_prop):
        QObject.__init__(self)
        self.hostname = hostname
        self.preview_prop = preview_prop
        self.selected_prop = selected_prop

        self.app = QApplication([])
        self.app.setApplicationName("Video Grid Mixer")
        self.grid = VideoGrid(self)
        self.selected_team = selected_prop.getValue()
        
        ranges = self.preview_prop.get("range").getValue().split(",")
        teams = []
        for tr in ranges:
            for i in range(int(tr.split("-")[0]),int(tr.split("-")[1])+1):
                teams.append(i)

        self.players = self.grid.addTeams(teams, teams_prop)
        self.selected_prop.addPropertyListener(TeamChangeListener(self))


    def run(self):
        self.grid.show()
        sys.exit(self.app.exec_())

    def selectTeam(self, team_id, update_redis):
        if team_id == self.selected_team:
            return
        print "Selected team ", team_id
        try:
            self.players[self.selected_team].setInactive()
        except KeyError:
            pass
        try:
            self.players[team_id].setActive()
        except KeyError:
            pass
        self.selected_team = team_id
        if update_redis:
            self.selected_prop.setValue(team_id)

class TeamChangeListener(prop.PropertyListener):
    def __init__(self, mixer):
        self.mixer = mixer
    
    def propertyChanged(self, changed_property):
        for player in self.mixer.grid.players.itervalues():
            player.emit(SIGNAL("select_team(int, bool)"), changed_property.getIntValue(), False)
            break
