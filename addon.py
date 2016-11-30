import time
import xbmc
import xbmcaddon
import json
import socket

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')


class MyPlayer(xbmc.Player):

    def __init__(self):
        xbmc.Player.__init__(self)

    def onPlayBackStarted(self):
        xbmc.log("Kodi Hue: DEBUG playback started called on player")
        if self.isPlayingVideo():
            state_changed("started")

    def onPlayBackPaused(self):
        xbmc.log("Kodi Hue: DEBUG playback paused called on player")
        if self.isPlayingVideo():
            state_changed("paused")

    def onPlayBackResumed(self):
        logger.debuglog("playback resumed called on player")
        if self.isPlayingVideo():
            state_changed("resumed")

    def onPlayBackStopped(self):
        xbmc.log("Kodi Hue: DEBUG playback stopped called on player")
        state_changed("stopped")

    def onPlayBackEnded(self):
        xbmc.log("Kodi Hue: DEBUG playback ended called on player")
        state_changed("stopped")


class Logger:
    scriptname = "Kodi Hue"
    enabled = True
    debug_enabled = False

    def log(self, msg):
        if self.enabled:
            xbmc.log("%s: %s" % (self.scriptname, msg))

    def debuglog(self, msg):
        if self.debug_enabled:
            self.log("DEBUG %s" % msg)

    def debug(self):
        self.debug_enabled = True

    def disable(self):
        self.enabled = False


class Yeelight:
    connected = None
    initial_state = ""

    def __init__(self):
        self.bulb_ip = __addon__.getSetting("light1_id")
        self.bulb_port = 55443

    def turnOff(self):
        message = {"id": 1, "method": "set_power", "params": ["off", "smooth", 500]}
        self.connect(message, self.bulb_ip, self.bulb_port)

    def turnOn(self):
        message = {"id": 1, "method": "set_power", "params": ["on", "smooth", 500]}
        self.connect(message, self.bulb_ip, self.bulb_port)

    def getState(self):
        message = {"id": 1, "method": "get_prop", "params": ["power"]}
        state = self.connect(message, self.bulb_ip, self.bulb_port)
        return json.loads(state)["result"][0]

    def connect(self, command, bulb_ip, bulb_port):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            msg = json.dumps(command) + "\r\n"
            tcp_socket.connect((bulb_ip, int(bulb_port)))
            tcp_socket.send(msg)
            data = tcp_socket.recv(1024)
            tcp_socket.close()
            return data
        except Exception as e:
            print "Unexpected error:", e


def showNotification(message):
    xbmc.executebuiltin('Notification(%s, %s, %s, %s)' %
                        (__addonname__, message, 3, __icon__))


def state_changed(state):
    if state == "started":
        mystate = yeelight.getState()
        yeelight.initial_state = mystate
        yeelight.turnOff()
    elif state == "resumed":
        yeelight.turnOff()
    elif state == "paused":
        yeelight.turnOn()
    elif state == "stopped":
        if yeelight.initial_state == "off":
            yeelight.turnOff()
        else:
            yeelight.turnOn()


if __name__ == '__main__':
    logger = Logger()

    monitor = xbmc.Monitor()
    yeelight = Yeelight()

    showNotification("Started")
    player = MyPlayer()
    while not monitor.abortRequested():
        if monitor.waitForAbort(1):
            break
