import httplib
import logging
import time
from math import atan2,degrees
import math

import socketIO_client
import random
import pygame
from pygame.locals import *
from pygame.color import THECOLORS
from functools import partial
import datetime

#logging.basicConfig()
reconnect = True
attack = True

firstConnect = False
projectiles = {}
playerDat = {'d':0}
pnbData = {}
chatLog = []
chatIdx = 0
numMines = 0
deadMines = 0
ourID = 'd'
ANGLES = []
dist = 0
angC = 0
nearPlan = 0
nearPlanDist = 0
CORrection = 0
ang = 0
shipAng = 0


eventMsgs = {'join':'JOINED!!!',
             'pnbcollision':'Tried to run over a planet. The planet won.',
             'disconnect':'LEFT!!!',
             'collision':'Person was run over!',
             'projectile':'Person was shot by a photon torpedo!'}

#logging.basicConfig(level=logging.DEBUG)



class ninjaClient:

    class EventHandler(socketIO_client.BaseNamespace):
        def on_connect( self):
            print "connected."
        
        def on_disconnect( self ):
            print "DISCONNECTED!"          
            if reconnect:
                client.Connect()
        def on_pos(self,data):
            global playerDat
            for k in data.keys():
                if playerDat.has_key(k): playerDat[k]['pos'].update(data[k])
                else: playerDat[k]['pos'] = data[k]
        def on_chat(self,data):
            chatLog.append(data)

        def on_shipstat(self,data):
            global playerDat
            
            for k in data.keys():
                
                if playerDat.has_key(k): playerDat[k].update(data[k])
                else: playerDat[k] = data[k]
                if data[k]['status'] == 'destroy':
                    playerDat.pop(k)

        def on_projstat(self,data):
            for k in data.keys():
                if data[k]['status'] == 'create':
                    if projectiles.has_key(k): projectiles[k].update(data[k])
                    else: projectiles[k] = data[k]
                else:
                    projectiles.pop(k)
        def on_projpos(self,data):
            for k in data.keys():
                projectiles[k].update(data[k])

            pass

        def on_pnbitsstat(self,data):
            global pnbData
            pnbData = data
    
    def getClosest(self,coord,projectiles):
        dist=lambda s,d: (s[0]-d[0])**2+(s[1]-d[1])**2 #a little function which calculates the distance between two coordinates
        pos = []
        for k in projectiles.keys():
            if projectiles[k].has_key('cssClass'):
                pos.append((200-int(projectiles[k]['pos']['x']/50),200-int(projectiles[k]['pos']['y']/50)))
            elif projectiles[k]['weaponID'] == 1:
                pos.append((200-int(projectiles[k]['pos']['x']/50),200-int(projectiles[k]['pos']['y']/50)))
        try:
            return min(pos, key=partial(dist, coord))
        except ValueError:
            return coord

    def GetName(self,key):
        try:
            return playerDat[key]['name']
        except:
            return ''

    def __init__(self):
        self.sio = socketIO_client.SocketIO('ninjanode.tn42.com',80, self.EventHandler)
        self.sio.timeout_in_seconds = 0.001
        self.ShipInfo = {'status':"create",
                         'name':"TheMineUNcrafter.py",
                         'style':"f"}
    def Connect(self):
        global firstConnect
        self.sio.emit('shipstat',self.ShipInfo)
        self.sio.wait(0.001)
        firstConnect = True

    def MoveForward(self,state):
        self.sio.emit('key',{'s':int(state), 'c': "u"})
        self.sio.wait(0.001)
    def MoveBackward(self,state):
        self.sio.emit('key',{'s':int(state), 'c': "d"})
        self.sio.wait(0.001)
    def MoveLeft(self,state):
        self.sio.emit('key',{'s':int(state), 'c': "l"})
        self.sio.wait(0.001)
    def MoveRight(self,state):
        self.sio.emit('key',{'s':int(state), 'c': "r"})
        self.sio.wait(0.001)
    def DropMine(self):
        self.sio.emit('key',{'s':1, 'c': "s"})
        self.sio.wait(0.001)
        self.sio.emit('key',{'s':0, 'c': "s"})
        self.sio.wait(0.001)
    def Fire(self):
        self.sio.emit('key',{'s':1, 'c': "f"})
        self.sio.wait(0.001)
        self.sio.emit('key',{'s':0, 'c': "f"})
        self.sio.wait(0.001)
    def MoveDegrees(self,deg,state):
        self.sio.emit('key',{'c':'m',
                             's':state,
                             'd': deg})
        self.sio.wait(0.001)

    def ChatSend(self,msg):
        self.sio.emit('chat', {'msg': str(msg)})
        self.sio.wait(0.001)

def GetAngle(p1, p2):
    xDiff = p2[0]-p1[0]
    yDiff= p2[1]-p1[1]
    return degrees(atan2(yDiff,xDiff))

client = ninjaClient()
client.Connect()
client.ChatSend('I am a bot written by Roger (theSteamRoller). My one goal is to obliterate the mines placed by the oppressors. ')

pygame.init()
window = pygame.display.set_mode((800,500))
screen = pygame.surface.Surface((400,400))
font = pygame.font.SysFont('console',18)
clock = pygame.time.Clock()


while True:
    client.sio.wait(0.001)
    clock.tick(0)
    if len(chatLog) > chatIdx:
        cht = chatLog[chatIdx]
        if cht['type'] == 'system':
            print client.GetName(cht['id']),'|',eventMsgs[cht['action']]

            if firstConnect:
                playerDat.pop(ourID)
                ourID = cht['id']
                firstConnect = False
        elif cht['type'] == 'chat':
            print client.GetName(cht['id']),'SAYS:',cht['msg']
            if '!info' in cht['msg'].lower():
                client.ChatSend('I am a bot written by Roger (theSteamRoller). My one goal is to obliterate the mines placed by the oppressors.')
            elif '!setcontroltome' in cht['msg'].lower():
                client.ChatSend('Control set to '+client.GetName(cht['id']))
            elif '!enable' in cht['msg'].lower()and 'Steam' in client.GetName(cht['id']):
                attack = True
                client.ChatSend('Phasers set to Kill! Mines, watch out!')

            elif '!disable' in cht['msg'].lower()and 'Steam' in client.GetName(cht['id']):
                attack = False
                client.ChatSend('Phasers set to Stun! Consider yourself lucky, mines!')
            elif '!toggle' in cht['msg'].lower() and 'Steam' in client.GetName(cht['id']):
                attack = not attack
                if attack:
                    client.ChatSend('Phasers set to Kill! Mines, watch out!')
                else:
                    client.ChatSend('Phasers set to Stun! Consider yourself lucky, mines!')

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
                client.ChatSend('Phasers set to Stun! Consider yourself lucky, mines!')
        elif event.key == 273:
            CORrection += 1
        elif event.key == 274:
            CORrection -= 1
        else:
            print event.key

    screen.fill((30,30,30))
    try:
        for k in playerDat.keys():
            if not playerDat[k]['status'] == 'boom':
                pos = (200-int(playerDat[k]['pos']['x']/50),200-int(playerDat[k]['pos']['y']/50))
                pygame.draw.circle(screen,THECOLORS[playerDat[k]['shieldStyle']],pos,4)

                if k == ourID:
                    closePos = client.getClosest(pos,projectiles)
                    shipAng = playerDat[k]['pos']['d']
                    ang = int(GetAngle(pos,closePos)) -90


                    if ang < 0: ang += 360
                    ANGLES.append(ang)

                    if len(ANGLES) > 5:
                        ANGLES.pop(0)
                    angC = ANGLES[-1] 

                    nearPlan = client.getClosest(pos,pnbData)
                    nearPlanDist = int(math.hypot(pos[0]-nearPlan[0], pos[1]-nearPlan[1]))


                    if attack:
                        pygame.draw.line(screen,THECOLORS['grey'],pos,closePos)

                    dist = int(math.hypot(pos[0]-closePos[0], pos[1]-closePos[1]))

                    if attack:
                        client.MoveDegrees(angC,0)
                        client.MoveDegrees(angC,1)
                        if dist < 10:
                            
                            client.Fire()
 
                        


    except BaseException as e:
        
        print e    
    for k in pnbData.keys():
        
        pos = (200-int(pnbData[k]['pos']['x']/50),200-int(pnbData[k]['pos']['y']/50))
        
        pygame.draw.circle(screen,THECOLORS['orange'],pos,pnbData[k]['radius']/50)

    o_numMines = numMines
    numMines = 0

    for k in projectiles.keys():
        if projectiles[k]['weaponID'] == 1:
            numMines += 1
            pos = (200-int(projectiles[k]['pos']['x']/50),200-int(projectiles[k]['pos']['y']/50))
            pygame.draw.circle(screen,THECOLORS[projectiles[k]['style']],pos,4, 1)

    if not o_numMines == numMines and o_numMines-1 == numMines:
        deadMines += 1
        #client.ChatSend(str(datetime.datetime.now())+' | Killed: '+str(deadMines))
        #client.ChatSend(str(numMines)+' Left!')
        #client.ChatSend('1 mine down! {0} left to go. This makes a total of {1} mines disarmed!'.format(numMines,deadMines))

    window.fill(THECOLORS['white'])
    window.blit(screen, (5,5))
    window.blit(font.render('# of mines disarmed:'+str(deadMines),1,THECOLORS['black']),(420,5))
    window.blit(font.render('# of mines left: '+str(numMines),1,THECOLORS['black']),(420,25))
    window.blit(font.render('Distance to target:'+str(dist),1,THECOLORS['black']),(420,85))
    window.blit(font.render('target Angle:'+str(ang),1,THECOLORS['black']),(420,105))
    window.blit(font.render('Dist to nearest planet:'+str(nearPlanDist),1,THECOLORS['black']),(420,125))
    window.blit(font.render('real angle  :'+str(ang-shipAng),1,THECOLORS['black']),(420,145))
    window.blit(font.render('correction:'+str(CORrection),1,THECOLORS['black']),(420,165))

    window.blit(font.render('# of players:'+str(len(playerDat)),1,THECOLORS['black']),(420,305))
    window.blit(font.render('FPS:'+str(int(clock.get_fps())),1,THECOLORS['black']),(420,325))
    
    pygame.display.update()