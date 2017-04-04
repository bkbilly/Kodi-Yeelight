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
    initial_state = []

    def __init__(self, ip):
        self.bulb_ip = ip
        self.bulb_port = 55443

    def turnOff(self):
        message = {"id": 1, "method": "set_power", "params": ["off", "smooth", 500]}
        self.connect(message, self.bulb_ip, self.bulb_port)

    def blueLight(self):
        message = {"id": 1, "method": "set_scene", "params": ["color", 1315890, 50]}
        self.connect(message, self.bulb_ip, self.bulb_port)

    def turnOn(self):
        message = {"id": 1, "method": "set_power", "params": ["on", "smooth", 500]}
        if self.initial_state[2] == "1":  # rgb mode
            message = {"id": 1, "method": "set_scene", "params": ["color", int(self.initial_state[4]), int(self.initial_state[1])]}
        elif self.initial_state[2] == "2": # white mode
            message = {"id": 1, "method": "set_scene", "params": ["ct", int(self.initial_state[3]), int(self.initial_state[1])]}
        elif self.initial_state[2] == "3": # hsv mode
            message = {"id": 1, "method": "set_scene", "params": ["hsv" , int(self.initial_state[5]), int(self.initial_state[6]), int(self.initial_state[1])]}
        self.connect(message, self.bulb_ip, self.bulb_port)

    def getState(self):
        message = {"id": 1, "method": "get_prop", "params": ["power", "bright", "color_mode", "ct", "rgb", "hue", "sat"]}
        state = self.connect(message, self.bulb_ip, self.bulb_port)
        return json.loads(state)["result"]

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
    if light_num >= 1:
        state_action(state,yeelight1)
    if light_num >= 2:
        state_action(state,yeelight2)

def state_action(state, bulb):
    if state == "started":
        bulb.initial_state = bulb.getState()
        if bulb.initial_state[0] == "on":
            bulb.blueLight()
    elif state == "resumed":
        if bulb.initial_state[0] == "on":
            bulb.blueLight()
    elif state == "paused":
        if bulb.initial_state[0] == "on":
            bulb.turnOn()
    elif state == "stopped":
        if bulb.initial_state[0] == "on":
            bulb.turnOn()
        else:
            bulb.turnOff()


if __name__ == '__main__':
    logger = Logger()

    monitor = xbmc.Monitor()
    
    light_num = int(__addon__.getSetting("light_num"))
    
    if light_num >= 1:
        yeelight1 = Yeelight(__addon__.getSetting("light1_id"))
    if light_num >= 2:
        yeelight2 = Yeelight(__addon__.getSetting("light2_id"))

    showNotification("Started")
    player = MyPlayer()
    while not monitor.abortRequested():
        if monitor.waitForAbort(1):
            break
