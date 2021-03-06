import sys
sys.path.append('C:\Python27\Lib\site-packages')

import logging
import time
import math
from math import atan2, degrees

import socketIO_client
import random
import pygame
from pygame.locals import *
from pygame.color import THECOLORS

from functools import partial
import datetime

# logging.basicConfig(level=logging.DEBUG)    #ENABLE THIS AT YOUR OWN
# RISK!!! FLOODS THE CONSOLE WITH ALL TRANSMITTED/RECIEVED PACKETS!

# Set to true to enable automatic reconnection after a disconnect
reconnect = True
# stores wether the bot is enabled or not. This will set the default state
# when it first logs on
attack = True
updates = True  # if this is true, then we say statistics ingame

# This is true if this is the first time connecting to the server
firstConnect = False
projectiles = {}  # dict storing all data about projectiles
playerDat = {'d': 0}  # dict storing all data about players
pnbData = {}  # dict storing planet data
# list that stores a log of all the chat events that have happened.
chatLog = []
chatIdx = 0  # index pointer to the current location in the chat log
numMines = 0  # number of mines on the current playing field
deadMines = 0  # number of mines we have killed
# stores our UUID. Set to 'd' so it does not cause an index error the
# first time it is loaded
ourID = 'd'
# I more or less don't use this anymore, it stores the last five or so angles.
ANGLES = []
dist = 0  # Distance from the current targer
angC = 0  # the angle sent to the server, after any math is completed.
nearPlan = 0  # the x,y position of the nearest planet to the bot.
nearPlanDist = 0  # the distance the bot is away from the nearest planet
ang = 0  # the angle that the ship needs to be at to fly straight at the target
shipAng = 0  # the current angle of the ship, as reported by the server
myMaster = ''  # Stores the UUID of the person with OP permissions for commands
velocity = {'x': 0,
            'y': 0,
            'd': 0,
            'l': 0}
newPos = (0, 0)
closePos = newPos

# messages printed to console on certain events.
eventMsgs = {'join': 'JOINED!!!',
             'pnbcollision': 'Tried to run over a planet. The planet won.',
             'disconnect': 'LEFT!!!',
             'collision': 'Person was run over!',
             'projectile': 'Person was shot by a photon torpedo!'}

targetPlayer = True
playerToTarget = 'docprofsky'
silentStart = True


class ninjaClient:

    """
    Contains all the stuff needed for socketIO and a few random other things
    """
    class EventHandler(socketIO_client.BaseNamespace):

        """
        Handles events from socketIO
        """

        def on_connect(self):
            # When we connect to the server. Simply print a debug message to
            # console
            print "connected."

        def on_disconnect(self):
            global myMaster
            print "DISCONNECTED!"  # When we get forcefully disconnected.
            if reconnect:  # if we want to reconnect, try it
                client.Connect()

        # wheb we recieve new information about player positions
        def on_pos(self, data):
            global playerDat  # make sure the variable is global
            # iterate through all the keys in the rcieved data
            for k in data.keys():
                if playerDat.has_key(k):
                    # if the player is already in the system, only overwrite
                    # the changes
                    playerDat[k]['pos'].update(data[k])
                else:
                    # otherwise, overwrite it all!
                    playerDat[k]['pos'] = data[k]

        def on_chat(self, data):  # when new data arrives from the chat system
            chatLog.append(data)  # add that data to the que

        def on_shipstat(self, data):  # recieved info on ships
            global playerDat  # globalize all the things!

            for k in data.keys():  # iterate through keys in recv'd data

                if playerDat.has_key(k):
                    # if the player is already in the system, only overwrite
                    # the changes
                    playerDat[k].update(data[k])
                else:
                    playerDat[k] = data[k]  # otherwise, overwrite it all!
                # If the player needs tobe removed from memory
                if data[k]['status'] == 'destroy':
                    playerDat.pop(k)

        def on_projstat(self, data):  # updates on projectiles status
            for k in data.keys():
                # if the projectile is being created
                if data[k]['status'] == 'create':
                    if projectiles.has_key(k):
                        # if the projectile is already in the system, only
                        # overwrite the changes
                        projectiles[k].update(data[k])
                    else:
                        # otherwise, overwrite it all!
                        projectiles[k] = data[k]
                else:
                    projectiles.pop(k)  # If we're not creating it, destroy it!

        def on_projpos(self, data):  # on position update of projectiles
            for k in data.keys():  # write new data to the dict
                projectiles[k].update(data[k])

        # This is only called once, on login, it gives data on PNBITS
        def on_pnbitsstat(self, data):
            global pnbData
            pnbData = data  # just copy the data into a global variable

    def getClosest(self, coord, projectiles):
        """
        returns closest coordinate to a coordinate (coord) from the list of coordinates (projectiles)
        """
        dist = lambda s, d: (s[0] - d[0]) ** 2 + (s[1] - d[
            1]) ** 2  # a little function which calculates the distance between two coordinates
        pos = []  # clear the local list of positions
        for k in projectiles.keys():
            if projectiles[k].has_key('cssClass'):  # if this is a planet
                # add the coordinates in a (0,0) fashion
                pos.append(
                    (200 - int(-projectiles[k]['pos']['x'] / 50), 200 - int(-projectiles[k]['pos']['y'] / 50)))
            elif projectiles[k]['weaponID'] == 1:  # or if this is a mine
                # add the coordinates in a (0,0) fashion
                pos.append(
                    (200 - int(-projectiles[k]['pos']['x'] / 50), 200 - int(-projectiles[k]['pos']['y'] / 50)))
        try:
            return min(pos, key=partial(dist, coord))
        except ValueError:
            return coord

    def GetName(self, key):
        try:
            return playerDat[key]['name']
        except:
            return ''

    def GetKey(self, name):
        try:
            for k in playerDat.keys():
                if playerDat[k]['name'] == name:
                    return k
        except BaseException as er:
            return ''

    def __init__(self, name="docprofsky"):
        self.sio = socketIO_client.SocketIO(
            'ninjanode.tn42.com', 80, self.EventHandler)
        self.sio.timeout_in_seconds = 0.001
        self.ShipInfo = {'status': "create",
                         'name': name,
                         'style': "c"}

    def Connect(self):
        global firstConnect
        self.sio.emit('shipstat', self.ShipInfo)
        self.sio.wait(0.001)
        firstConnect = True

    def MoveForward(self, state):
        self.sio.emit('key', {'s': int(state), 'c': "u"})
        self.sio.wait(0.001)

    def MoveBackward(self, state):
        self.sio.emit('key', {'s': int(state), 'c': "d"})
        self.sio.wait(0.001)

    def MoveLeft(self, state):
        self.sio.emit('key', {'s': int(state), 'c': "l"})
        self.sio.wait(0.001)

    def MoveRight(self, state):
        self.sio.emit('key', {'s': int(state), 'c': "r"})
        self.sio.wait(0.001)

    def DropMine(self):
        self.sio.emit('key', {'s': 1, 'c': "s"})
        self.sio.wait(0.001)
        self.sio.emit('key', {'s': 0, 'c': "s"})
        self.sio.wait(0.001)

    def Fire(self):
        self.sio.emit('key', {'s': 1, 'c': "f"})
        self.sio.wait(0.001)
        self.sio.emit('key', {'s': 0, 'c': "f"})
        self.sio.wait(0.001)

    def MoveDegrees(self, deg, state):
        self.sio.emit('key', {'c': 'm',
                              's': state,
                              'd': deg})
        self.sio.wait(0.001)

    def ChatSend(self, msg):
        self.sio.emit('chat', {'msg': str(msg)})
        self.sio.wait(0.001)


def GetAngle(p1, p2):
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    return degrees(atan2(yDiff, xDiff))


def GetNextPos(angle, posX, posY, velX, velY, length, sec=1):
    global closePos, Estang
    velX = int(-velX / (50 / 6))
    velY = int(-velY / (50 / 6))
    len = int(length / (50))
    X = posX + velY
    Y = posY + velX

    return (X, Y)

if len(sys.argv) == 3:
    client = ninjaClient(sys.argv[1])
    playerToTarget = sys.argv[2]
elif len(sys.argv) == 2:
    client = ninjaClient(sys.argv[1])
else:
    client = ninjaClient('!docprofsky')

client.Connect()

if not silentStart:
    client.ChatSend(
        'I am a bot written by Roger . My one goal is to obliterate the mines placed by the oppressors. ')

pygame.init()
window = pygame.display.set_mode((800, 500))
screen = pygame.surface.Surface((400, 400))
font = pygame.font.SysFont('console', 18)
clock = pygame.time.Clock()

fonts = pygame.font.SysFont('console', 8, True)
while True:
    client.sio.wait(0.001)
    clock.tick(0)

    client.Fire()
    client.DropMine()
    if len(chatLog) > chatIdx:
        cht = chatLog[chatIdx]
        if cht['type'] == 'system':
            print client.GetName(cht['id']), '|', eventMsgs[cht['action']]

            if firstConnect:
                playerDat.pop(ourID)
                ourID = cht['id']
                firstConnect = False

        elif cht['type'] == 'chat':
            print client.GetName(cht['id']), 'SAYS:', cht['msg']
            if '!info' in cht['msg'].lower():
                client.ChatSend(
                    'I am a bot written by Roger . My one goal is to obliterate the mines placed by the oppressors.')

            elif '!setcontroltome' in cht['msg'].lower():
                if len(myMaster) == 0:
                    client.ChatSend('Control set to {0} ({1})! We shall forever be in your service!'.format(
                        client.GetName(cht['id']), cht['id']))
                    myMaster = cht['id']
            elif '!enable' in cht['msg'].lower()and myMaster == cht['id']:
                attack = True
                client.ChatSend('Phasers set to Kill! Mines, watch out!')

            elif '!disable' in cht['msg'].lower()and myMaster == cht['id']:
                attack = False
                client.ChatSend(
                    'Phasers set to Stun! Consider yourself lucky, mines!')
                #attack = True
                #client.ChatSend('Theres no disabling me!')

            elif '!toggle' in cht['msg'].lower() and myMaster == cht['id']:
                attack = not attack
                if attack:
                    client.ChatSend('Phasers set to Kill! Mines, watch out!')
                else:
                    client.ChatSend(
                        'Phasers set to Stun! Consider yourself lucky, mines!')

            elif '!kill' in cht['msg'].lower() and myMaster == cht['id']:
                targetPlayer = not targetPlayer
                if targetPlayer:
                    client.ChatSend('Now Targeting: ' + playerToTarget)
                else:
                    client.ChatSend('Player Targeting Disabled!')

            elif '!newtarget' in cht['msg'].lower() and myMaster == cht['id']:
                playerToTarget = cht['msg'].replace('!newtarget', '').strip()
                client.ChatSend('Now Targeting: ' + playerToTarget)

            elif '!updates' in cht['msg'].lower():
                updates = not updates
                if updates:
                    client.ChatSend(
                        'I shall now spam this clean chat log with useless messages!')
                else:
                    client.ChatSend('You are now free of my spam!')

            elif '!stats' in cht['msg'].lower():

                client.ChatSend('Disarmed {0} mines out of {1} remaining mines. \
                                 Current TPS is {2}. My UUID is: {3}.  \
                                 My current owner is: {4} ({5})' .format(deadMines,
                                                                         numMines,
                                                                         clock.get_fps(),
                                                                         ourID,
                                                                         myMaster,
                                                                         client.GetName(
                                                                             myMaster)
                                                                         ))
        else:
            print cht
        chatIdx += 1

    event = pygame.event.poll()
    if event.type == KEYDOWN:
        if event.key == 107:
            attack = not attack
            if attack:
                client.ChatSend('Phasers set to Kill! Mines, watch out!')
            else:
                client.ChatSend(
                    'Phasers set to Stun! Consider yourself lucky, mines!')
        else:
            print event.key
    elif event.type == QUIT:
        pygame.quit()
        exit()

    screen.fill((30, 30, 30))
    try:
        for k in playerDat.keys():
            if not playerDat[k]['status'] == 'boom':
                pos = (
                    200 - int(-playerDat[k]['pos']['x'] / 50), 200 - int(-playerDat[k]['pos']['y'] / 50))
                pygame.draw.circle(
                    screen, THECOLORS[playerDat[k]['shieldStyle']], pos, 4)
                screen.blit(fonts.render(
                    playerDat[k]['name'], 1, (255, 255, 255)), (pos[0] + 5, pos[1] - 5))

                if k == ourID:
                    if targetPlayer:
                        tID = client.GetKey(playerToTarget)
                        # print 'TID', tID
                        closePos = (
                            200 - int(-playerDat[tID]['pos']['x'] / 50), 200 - int(-playerDat[tID]['pos']['y'] / 50))
                    else:
                        closePos = client.getClosest(pos, projectiles)
                    shipAng = playerDat[k]['pos']['d']
                    ang = int(GetAngle(pos, closePos)) - 90

                    velocity = playerDat[ourID]['pos']['vel']
                    velocity = {'x': -velocity['x'],
                                'y': -velocity['y'],
                                'l': -velocity['l'],
                                't': -velocity['t']}
                    newPos = GetNextPos(int(velocity['t']),
                                        pos[0],
                                        pos[1],
                                        int(velocity['x']),
                                        int(velocity['y']),
                                        int(velocity['l']))
                    ang = ang - int(GetAngle(pos, newPos))
                    if ang < 0:
                        ang += 360
                    Newang = GetAngle(newPos, closePos) + 90
                    if Newang < 0:
                        Newang += 360

                    angC = int(Newang)

                    nearPlan = client.getClosest(pos, pnbData)
                    nearPlanDist = int(
                        math.hypot(pos[0] - nearPlan[0], pos[1] - nearPlan[1]))

                    # print angC
                    if attack:
                        pygame.draw.line(
                            screen, THECOLORS['grey'], pos, closePos)

                    pygame.draw.line(
                        screen, THECOLORS['red'], newPos, closePos)

                    dist = int(
                        math.hypot(pos[0] - closePos[0], pos[1] - closePos[1]))

                    if attack:
                        client.MoveDegrees(angC, 0)
                        client.MoveDegrees(angC, 1)
                        if dist < 10:
                            client.Fire()
                            GetAngle(pos, newPos)

    except BaseException as e:
        print e
    for k in pnbData.keys():

        pos = (200 - int(-pnbData[k]['pos']['x'] / 50),
               200 - int(-pnbData[k]['pos']['y'] / 50))

        pygame.draw.circle(
            screen, THECOLORS['orange'], pos, pnbData[k]['radius'] / 50)

    o_numMines = numMines
    numMines = 0

    for k in projectiles.keys():
        if projectiles[k]['weaponID'] == 1:
            numMines += 1
            pos = (
                200 - int(-projectiles[k]['pos']['x'] / 50), 200 - int(-projectiles[k]['pos']['y'] / 50))
            pygame.draw.circle(
                screen, THECOLORS[projectiles[k]['style']], pos, 4, 1)

    if not o_numMines == numMines and o_numMines - 1 == numMines:
        deadMines += 1
        #client.ChatSend(str(datetime.datetime.now())+' | Killed: '+str(deadMines))
        #client.ChatSend(str(numMines)+' Left!')

        if updates:
            client.ChatSend('1 mine down! {0} left to go. This makes a total of {1} mines disarmed! {2}'.format(
                numMines, deadMines, datetime.datetime.now()))

    window.fill(THECOLORS['white'])
    #screen = pygame.transform.flip(screen, 180, 180)
    window.blit(screen, (5, 5))
    window.blit(font.render(
        '# of mines disarmed:' + str(deadMines), 1, THECOLORS['black']), (420, 5))
    window.blit(font.render(
        '# of mines left: ' + str(numMines), 1, THECOLORS['black']), (420, 25))
    window.blit(font.render(
        'Distance to target:' + str(dist), 1, THECOLORS['black']), (420, 85))
    window.blit(
        font.render('target Angle:' + str(angC), 1, THECOLORS['black']), (420, 105))
    window.blit(font.render('Dist to nearest planet:' +
                            str(nearPlanDist), 1, THECOLORS['black']), (420, 125))
    window.blit(font.render('Dif of cur ang and target ang:' +
                            str(ang - shipAng), 1, THECOLORS['black']), (420, 145))
    window.blit(font.render(
        'Future angle:' + str(int(GetAngle(pos, newPos))), 1, THECOLORS['black']), (420, 165))
    window.blit(font.render(
        'Velocity X:' + str(int(velocity['x'])), 1, THECOLORS['black']), (420, 185))
    window.blit(font.render(
        'Velocity Y:' + str(int(velocity['y'])), 1, THECOLORS['black']), (420, 205))

    window.blit(font.render(
        '# of players:' + str(len(playerDat)), 1, THECOLORS['black']), (420, 305))
    window.blit(font.render(
        'TPS:' + str(int(clock.get_fps())), 1, THECOLORS['black']), (420, 325))

    try:
        pygame.display.set_caption("T: %s M: %s C: %s" % (
            playerToTarget, playerDat[ourID]['name'], client.GetName(myMaster)))
    except:
        pass
    pygame.display.update()
