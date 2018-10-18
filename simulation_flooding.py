#!/usr/bin/env python2

import simpy
import random
import numpy as np
import math
import sys
import matplotlib.pyplot as plt
import matplotlib.image as mpimg



# turn on/off graphics
graphics = 1

# do the full collision check
full_collision = False

#speed of light
c = 299792.458 # m/ms
map = [[663, 785, 802, 631, 635, 525, 759, 425, 332, 651, 117, 80, 1085, 432, 836, 288, 791, 1100, 927, 197, 880, 281, 630, 259, 962, 529, 952, 736, 443, 746],
               [836, 534, 712, 647, 229, 389, 82, 594, 323, 489, 442, 634, 337, 699, 178, 618, 369, 457, 88, 282, 310, 488,
                360, 699, 201, 566, 561, 214, 271, 1]]
# this is an array with measured values for sensitivity
# see paper, Table 3
sf7 = np.array([7,-126.5,-124.25,-120.75])
sf8 = np.array([8,-127.25,-126.75,-124.0])
sf9 = np.array([9,-131.25,-128.25,-127.5])
sf10 = np.array([10,-132.75,-130.25,-128.75])
sf11 = np.array([11,-134.5,-132.75,-128.75])
sf12 = np.array([12,-133.25,-132.25,-132.25])

#result from experiment result
#this is an array with measured PRR (depending on timing offset )of 2 packet having power_offset = 0
#T_offset/Tsymb#  0       1/8     2/8    3/8     4/8    5/8    6/8    7/8     8/8
PRR_0 = np.array([0.8383, 0.8883, 0.9516, 0.9533, 0.9733, 0.97, 0.9467, 0.925, 0.8383])

# Power Offset = [1 - 3]
PRR_2_0 = np.array([0.56, 0.52, 0.48, 0.72, 0.86, 0.80, 0.4, 0.2, 0.26])
P20_first = np.array([1, 1, 0.875, 0.61, 0.51, 0.45, 0.3, 0.9, 1])

PRR_2_1 = np.array([0.56, 0.48, 0.7, 0.94, 0.92, 0.98, 0.94, 0.4, 0.3])
P21_first = np.array([0, 1, 0.92, 0.94, 1, 0.89, 1, 1, 1])

#power offset = [3 - 6]
PRR_4_0 = np.array([0.96, 0.68, 0.94, 1, 0.92, 1, 1, 0.9, 0.58])
P40_first = np.array([0, 0, 0, 0, 0.04, 0, 0, 0, 0])

PRR_4_1 = np.array([0.96, 1, 1, 1, 0.92, 0.98, 0.78, 0.78, 0.64])
P41_first = np.array([1, 1, 1, 1, 0.93, 0.86, 1, 1, 1])

def distance(id1,id2):
    scale = 0.68
    return int(np.sqrt((nodes[id1].x - nodes[id2].x) * (nodes[id1].x - nodes[id2].x) + (nodes[id1].y - nodes[id2].y) * (nodes[id1].y - nodes[id2].y))*scale)

#
# check for collisions at base station
# Note: called before a packet (or rather node) is inserted into the list

def checkcollision(packet, inNode):
    col = 0 # flag needed since there might be several collisions for packet
    processing = 0
    for i in range(0, len(inNode.rxlist)):
        if inNode.rxlist[i].packet.processed == 1:
            processing = processing + 1

    packet.processed = 1

    if inNode.rxlist:
        print("CHECK node {}  others: {}".format(packet.nodeid, len(inNode.rxlist)))
        for other in inNode.rxlist:
            if other.nodeid != packet.nodeid:
               print(">> node {} (sf:{} bw:{} freq:{:.6e})".format(
                   other.nodeid, other.packet.sf, other.packet.bw, other.packet.freq))
               tsymb = (2.0**packet.sf)/packet.bw
               print ("TSYMB: ", tsymb)
               # simple collision
               if frequencyCollision(packet, other.packet) \
                   and sfCollision(packet, other.packet):

                   if timingCollision(packet, other.packet, inNode):
                       # check who collides in the power domain
                       c = powerCollision(packet, other.packet, tsymb, inNode)
                       # mark all the collided packets
                       # either this one, the other one, or both
                       for p in c:
                           inNode.collided[p.nodeid] = 1
                           if p == packet:
                               col = 1
                   else:
                       # no timing collision, all fine
                       pass

        return col
    return 0

#
# frequencyCollision, conditions
#
#        |f1-f2| <= 120 kHz if f1 or f2 has bw 500
#        |f1-f2| <= 60 kHz if f1 or f2 has bw 250
#        |f1-f2| <= 30 kHz if f1 or f2 has bw 125
def frequencyCollision(p1,p2):
    if (abs(p1.freq-p2.freq)<=120 and (p1.bw==500 or p2.freq==500)):
        #print("frequency coll 500")
        return True
    elif (abs(p1.freq-p2.freq)<=60 and (p1.bw==250 or p2.freq==250)):
        #print("frequency coll 250")
        return True
    else:
        if (abs(p1.freq-p2.freq)<=30):
            #print("frequency coll 125")
            return True
        #else:
    #print("no frequency coll")
    return False

def sfCollision(p1, p2):
    if p1.sf == p2.sf:
        #print("collision sf node {} and node {}".format(p1.nodeid, p2.nodeid))
        # p2 may have been lost too, will be marked by other checks
        return True
    #print("no sf collision")
    return False

def powerCollision(p1, p2, tsymb, inNode):
    powerThreshold = 6 # dB
    print("CHECKING POWER COLLISION: AT: ",inNode.nodeid ," --- NODE: ", p1.nodeid,"  ---NODE: ", p2.nodeid)
    print("PWR: NODE: ", p1.nodeid, " RSSI: ", inNode.rssi[p1.nodeid] ,"NODE: ", p2.nodeid, " RSSI: ", \
          inNode.rssi[p2.nodeid] , "---DIFF:", round(inNode.rssi[p1.nodeid] - inNode.rssi[p2.nodeid],2))
    print("TIMING: NODE: ", p1.nodeid, "ARRIVE TIME: ",inNode.arriveTime[p1.nodeid], "--- NODE: ", p2.nodeid, "ARRIVE TIME: ",inNode.arriveTime[p2.nodeid])
    if abs(inNode.rssi[p1.nodeid] - inNode.rssi[p2.nodeid]) < powerThreshold:
        # power offset <= 1
        if abs(inNode.rssi[p1.nodeid] - inNode.rssi[p2.nodeid]) <= 1:
            #need to add more condition
            #calculate timing offset between 2 packet
            time_offset = abs(inNode.arriveTime[p1.nodeid] - inNode.arriveTime[p2.nodeid])
            #scale timing offset in range 1 symbol time
            scale_time_offset = 0
            i = 0
            while True:
                if(tsymb * i > time_offset):
                    scale_time_offset = (time_offset - tsymb * (i - 1))/tsymb
                    break
                else:
                    i = i + 1
            print ("scale_time_offset: ",scale_time_offset)
            prr = 0
            for x in range(1,9):
                if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                    prr = (PRR_0[x] - PRR_0[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + PRR_0[x - 1]
                    print("PRR: ", prr)
                    break
            myRand = random.uniform(0, 1)
            print ("random number: ", myRand)
            if(myRand <= prr):
                if(inNode.arriveTime[p1.nodeid] > inNode.arriveTime[p2.nodeid]):
                    print("PKT OF NODE: ",p2.nodeid," is COLLIDED: CT effect")
                    return (p1, )
                else:
                    print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                    return (p2, )
            else:
                print ("Both are COLLIDED: CT effect")
                return (p1, p2)
        elif (abs(inNode.rssi[p1.nodeid] - inNode.rssi[p2.nodeid]) <= 3) and (abs(inNode.rssi[p1.nodeid] - inNode.rssi[p2.nodeid]) > 1):
            # power offset > 1 and power offset <3
            sign = inNode.arriveTime[p1.nodeid] - inNode.arriveTime[p2.nodeid]
            # scale timing offset in range 1 symbol time
            time_offset = abs(sign)
            scale_time_offset = 0
            i = 0
            while True:
                if (tsymb * i > time_offset):
                    scale_time_offset = (time_offset - tsymb * (i - 1)) / tsymb
                    break
                else:
                    i = i + 1
            print("scale_time_offset: ", scale_time_offset)
            prr = 0
            if ((sign >= 0) and (inNode.rssi[p1.nodeid] > inNode.rssi[p2.nodeid])) or ((sign <= 0) and (inNode.rssi[p1.nodeid] < inNode.rssi[p2.nodeid])) :    #weaker arrive first
                print ("weaker transmission arrive firstly")
                for x in range(1, 9):
                    if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                        prr = (PRR_2_0[x] - PRR_2_0[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + PRR_2_0[x - 1]
                        print("PRR: ", prr)
                        break
                myRand = random.uniform(0, 1)
                print("random number: ", myRand)
                if (myRand <= prr):
                    ratio =0
                    for x in range(1, 9):
                        if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                            ratio = (P20_first[x] - P20_first[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + P20_first[x - 1]
                            print("p1_ratio: ", ratio)
                            break
                    ran_ratio = random.uniform(0, 1)
                    print("ran_ratio: ", ran_ratio)
                    if (ran_ratio < ratio):
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                    else:
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                else:
                    print("Both are COLLIDED: CT effect")
                    return (p1, p2)
            else:       #stronger transmission arrive first
                print("stronger transmission arrive firstly")
                for x in range(1, 9):
                    if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                        prr = (PRR_2_1[x] - PRR_2_1[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + PRR_2_1[x - 1]
                        print("PRR: ", prr)
                        break
                myRand = random.uniform(0, 1)
                print("random number: ", myRand)
                if (myRand <= prr):
                    ratio =0
                    for x in range(1, 9):
                        if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                            ratio = (P21_first[x] - P21_first[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + P21_first[x - 1]
                            print("p1_ratio: ", ratio)
                            break
                    ran_ratio = random.uniform(0, 1)
                    print("ran_ratio: ", ran_ratio)
                    if (ran_ratio < ratio):
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                    else:
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                else:
                    print("Both are COLLIDED: CT effect")
                    return (p1, p2)
        else:
            # power offset > 3 and power offset <6
            sign = inNode.arriveTime[p1.nodeid] - inNode.arriveTime[p2.nodeid]
            # scale timing offset in range 1 symbol time
            time_offset = abs(sign)
            scale_time_offset = 0
            i = 0
            while True:
                if (tsymb * i > time_offset):
                    scale_time_offset = (time_offset - tsymb * (i - 1)) / tsymb
                    break
                else:
                    i = i + 1
            print("scale_time_offset: ", scale_time_offset)
            prr = 0
            if ((sign >= 0) and (inNode.rssi[p1.nodeid] > inNode.rssi[p2.nodeid])) or ((sign <= 0) and (inNode.rssi[p1.nodeid] < inNode.rssi[p2.nodeid])) :    #weaker arrive first
                print("weaker transmission arrive firstly")
                for x in range(1, 9):
                    if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                        prr = (PRR_4_0[x] - PRR_4_0[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + PRR_4_0[x - 1]
                        print("PRR: ", prr)
                        break
                myRand = random.uniform(0, 1)
                print("random number: ", myRand)
                if (myRand <= prr):
                    ratio =0
                    for x in range(1, 9):
                        if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                            ratio = (P40_first[x] - P40_first[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + P40_first[x - 1]
                            print("p2_ratio: ", ratio)
                            break
                    ran_ratio = random.uniform(0, 1)
                    print("ran_ratio: ", ran_ratio)
                    if (ran_ratio < ratio):
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                    else:
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                else:
                    print("Both are COLLIDED: CT effect")
                    return (p1, p2)
            else:       #stronger transmission arrive first
                print("stronger transmission arrive firstly")
                for x in range(1, 9):
                    if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                        prr = (PRR_4_1[x] - PRR_4_1[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + PRR_4_1[x - 1]
                        print("PRR: ", prr)
                        break
                myRand = random.uniform(0, 1)
                print("random number: ", myRand)
                if (myRand <= prr):
                    ratio =0
                    for x in range(1, 9):
                        if (scale_time_offset >= ((x - 1) / 8)) and (scale_time_offset <= (x / 8)):
                            ratio = (P41_first[x] - P41_first[x - 1]) * (scale_time_offset - (x - 1) / 8) / 0.125 + P41_first[x - 1]
                            print("p2_ratio: ", ratio)
                            break
                    ran_ratio = random.uniform(0, 1)
                    print("ran_ratio: ", ran_ratio)
                    if (ran_ratio < ratio):
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                    else:
                        if sign>=0:     #p2 arrive first
                            print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: CT effect")
                            return (p2,)
                        else:           #p1 arrive first
                            print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: CT effect")
                            return (p1,)
                else:
                    print("Both are COLLIDED: CT effect")
                    return (p1, p2)
    else:
        #capture effect
        if(inNode.rssi[p1.nodeid] > inNode.rssi[p2.nodeid]):
            if inNode.arriveTime[p1.nodeid] - inNode.arriveTime[p2.nodeid] < (3* tsymb):
                print("PKT OF NODE: ", p2.nodeid, " is COLLIDED: capture effect")
                return (p2, )
            else:
                print("Both are COLLIDED: capture effect")
                return (p1, p2)
        else:
            if inNode.arriveTime[p2.nodeid] - inNode.arriveTime[p1.nodeid] < (3 * tsymb):
                print("PKT OF NODE: ", p1.nodeid, " is COLLIDED: capture effect")
                return (p1, )
            else:
                print("Both are COLLIDED: capture effect")
                return (p1, p2)

def timingCollision(p1, p2, inNode):
    # assuming p1 is the freshly arrived packet and this is the last check
    # we've already determined that p1 is a weak packet, so the only
    # way we can win is by being late enough (only the first n - 5 preamble symbols overlap)

    # assuming 8 preamble symbols
    Npream = 8

    # we can lose at most (Npream - 5) * Tsym of our preamble
    Tpreamb = 2**p1.sf/(1.0*p1.bw) * (Npream - 5)

    # check whether p2 ends in p1's critical section
    p2_end = inNode.arriveTime[p2.nodeid] + p2.rectime
    p1_cs = env.now + Tpreamb
    # print("collision timing node {} ({},{},{}) node {} ({},{})".format(
    #     p1.nodeid, env.now - env.now, p1_cs - env.now, p1.rectime,
    #     p2.nodeid, p2.txTime - env.now, p2_end - env.now)
    # )
    if p1_cs < p2_end:
        # p1 collided with p2 and lost
        print ("OVERLAP")
        return True
    print("NOT OVERLAP")
    return False

# this function computes the airtime of a packet
# according to LoraDesignGuide_STD.pdf
#
def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    print("sf", sf, " cr", cr, "pl", pl, "bw", bw)
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload

#
# this function creates a node
#
class myNode():
    def __init__(self, nodeid, radio_mode, packetlen,_x,_y, env):
        self.env = env
        self.action = env.process(operate(env,self))
        self.nodeid = nodeid
        self.radio_mode = radio_mode
        self.parentId = None
        self.rank = -1 # init rank as -1
        self.x = _x
        self.y = _y
        self.rxlist = []
        self.last_check_index = -1
        self.packet = myPacket(self.nodeid, packetlen)
        self.sent = 0
        self.maxDepth = 0

        #list of packet this node can overhear during simulation
        self.overhearList = []
        global nrNodes
        self.rssi = [None]*nrNodes
        self.collided = [None]*nrNodes
        self.arriveTime = [None]*nrNodes

        print("nrNodes: ",nrNodes)
        for i in range(0, nrNodes):
            self.rssi[i] = 0
            self.collided[i] = 0
            self.arriveTime[i] = 0

        # found = 0
        # global nodes
        temp_sensitivity = sensi[self.packet.sf - 7, [125, 250, 500].index(self.packet.bw) + 1]
        # #place node onto area such as it is in transmission range of at least 1 node
        # while True:
        #     temp_posx = random.randint(0, xmax)
        #     temp_posy = random.randint(0, xmax)
        #     if(len(nodes) == 0):
        #         print("FIRST NODE")
        #         self.x = temp_posx
        #         self.y = temp_posy
        #         found = 1
        #         break
        #     else:
        #         for n in nodes:
        #             dist = np.sqrt(((abs(n.x - temp_posx)) ** 2) + ((abs(n.y - temp_posy)) ** 2))
        #             temp_Lpl = Lpld0 + 10 * gamma * math.log10(dist / d0)
        #             temp_Prx = self.packet.txpow - GL - temp_Lpl
        #             if temp_Prx >= temp_sensitivity:
        #                 self.x = temp_posx
        #                 self.y = temp_posy
        #                 found = 1
        #                 break
        #         if found == 1:
        #             break
        #     print("RE_PLACE POSITION")
        print('node %d' %nodeid, "x", self.x, "y", self.y)
        maxDistance = d0*(10**((self.packet.txpow - Lpld0 - temp_sensitivity)/(10*gamma)))
        print("maxDistance : ", maxDistance)
        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            #plt.pause(1)
            if nodeid==0:
                ax.add_artist(plt.Circle((self.x, self.y), 8, fill=True, color='red'))
                ax.add_artist(plt.Circle((self.x, self.y), maxDistance, fill=False, color='red'))
                ax.text(self.x -8, self.y+12, str(self.nodeid), color="red", fontsize=8)
            else:
                ax.add_artist(plt.Circle((self.x, self.y), 8, fill=True, color='blue'))
                #ax.add_artist(plt.Circle((self.x, self.y), maxDistance, fill=False, color='red'))
                ax.text(self.x - 8, self.y +12, str(self.nodeid), color="red", fontsize=8)

#
# this function creates a packet (associated with a node)
# it also sets all parameters, currently random
#
class myPacket():
    def __init__(self, nodeid, plen):
        global CT_INSERT_ENABLE
        global Ptx
        global gamma
        global d0
        global var
        global Lpld0
        global GL

        self.nodeid = nodeid
        self.txpow = Ptx

        self.sf = 12    #SF12
        self.cr = 1     #CR4/5
        self.bw = 125   #BW125



        # transmission range, needs update XXX
        self.pl = plen
        self.symTime = (2.0**self.sf)/self.bw
        if CT_INSERT_ENABLE==1:
            self.insertDelay = self.symTime*random.randint(0, 32)/32
            print("insertDelay: ", self.insertDelay)
        else:
            self.insertDelay = 0
            print("insertDelay: ", self.insertDelay)
        self.txTime = None  #the actual sending time
        # frequencies: lower bound + number of 61 Hz steps
        self.freq = 860000000
        print("frequency" ,self.freq, "symTime ", self.symTime)
        print("bw", self.bw, "sf", self.sf, "cr", self.cr)
        self.rectime = airtime(self.sf,self.cr,self.pl,self.bw)
        print("rectime node ", self.nodeid, "  ", self.rectime)
        self.processed = 0

def proc_interupt(env, node):
    yield env.timeout(0)
    node.action.interrupt()


def operate(env,node):
    yield env.timeout(0)
    if(node.radio_mode is 'rx'):
        try:
            yield env.timeout(1000000)
        except simpy.Interrupt:
            print("NODE: ", node.nodeid," --INTERRUPT: CHANGE TO TX MODE")
    if(node.radio_mode is 'tx'):
        print("TX MODE:")

        sensitivity = sensi[node.packet.sf - 7, [125, 250, 500].index(node.packet.bw) + 1]
        node.radio_mode = 'sleep'
        global InsertDelay
        if CT_INSERT_ENABLE == 1 or CT_INSERT_ENABLE == 2:
            node.packet.txTime = env.now + node.packet.insertDelay
        else:
            node.packet.txTime = env.now
        node.sent = node.sent + 1
        for rx_node in nodes:
            if (rx_node.radio_mode is 'rx'):
                distance = np.sqrt(
                    (node.x - rx_node.x) * (node.x - rx_node.x) + (node.y - rx_node.y) * (node.y - rx_node.y))
                Lpl = Lpld0 + 10 * gamma * math.log10(distance / d0)
                print("Lpl:", Lpl)
                Prx = rx_node.packet.txpow - GL - Lpl
                if Prx < sensitivity:
                    print("NODE ", node.nodeid, " OUT OF range transmission of NODE ", rx_node.nodeid)
                else:
                    rx_node.rssi[node.nodeid] = Prx
                    rx_node.arriveTime[node.nodeid] = node.packet.txTime #+ distance / c  # plus propagation time
                    # check collision
                    print("NODE ", node.nodeid, " IN range transmission of NODE ", rx_node.nodeid, "distance", distance, \
                          "at txTime", node.packet.txTime, "arriveTime", rx_node.arriveTime[node.nodeid])
                    if (checkcollision(node.packet,rx_node) == 1):
                        print("COLLIDED")
                        rx_node.collided[node.nodeid] = 1
                    else:
                        print("NOT COLLIDED")
                        rx_node.collided[node.nodeid] = 0
                    rx_node.overhearList.append(node)
                    rx_node.rxlist.append(node)
        if CT_INSERT_ENABLE == 1:
            txdelay = node.packet.symTime
        elif CT_INSERT_ENABLE == 2:
            txdelay = node.packet.insertDelay
        else:
            txdelay = 0
        yield env.timeout(node.packet.rectime + txdelay)
        for rx_node in nodes:
            if (rx_node.radio_mode is 'rx'):
                if (node in rx_node.rxlist):
                    change = False
                    if(rx_node.collided[node.nodeid] == 0):
                        change = True
                        rx_node.parentId = node.nodeid
                        rx_node.rank = node.rank + 1
                        print("NODE: ",rx_node.nodeid, "----RANK: ", rx_node.rank, "----Parent_Node: ", rx_node.parentId)
                    else:
                        print("NODE: ", node.nodeid, "COLLIDED in receiver NODE: ", rx_node.nodeid)
                    print("remove packet of NODE: ", node.nodeid, "from rx list of NODE: ", rx_node.nodeid)
                    rx_node.rxlist.remove(node)
                    if(change):
                        print("NODE: ", rx_node.nodeid, "are changing to TX MODE")
                        rx_node.radio_mode = 'tx'
                        env.process(proc_interupt(env, rx_node))


def receive(env, node):
    global Ptx
    global gamma
    global d0
    global var
    global Lpld0
    global GL
    sensitivity = sensi[node.packet.sf - 7, [125, 250, 500].index(node.packet.bw) + 1]

    for temp_node in packetsInNetwork[node.last_check_index + 1: len(packetsInNetwork)]:
        node.last_check_index = node.last_check_index + 1
        distance = np.sqrt((node.x-temp_node.x)*(node.x-temp_node.x)+(node.y-temp_node.y)*(node.y-temp_node.y))
        Lpl = Lpld0 + 10 * gamma * math.log10(distance / d0)
        print("Lpl:", Lpl)
        Prx = temp_node.packet.txpow - GL - Lpl
        if Prx < sensitivity:
            print("node ", node.nodeid," OUT OF range transmission of node ", temp_node.nodeid)
        else:
            temp_node.rssi = Prx
            temp_node.packet.arriveTime = temp_node.packet.txTime + distance/c # plus propagation time
            # if (checkcollision(node.packet) == 1):
            #     node.packet.collided = 1
            # else:
            #     node.packet.collided = 0
            node.rxlist.append(temp_node)
            #check collision
            print("node ", node.nodeid, " IN range transmission of node ", temp_node.nodeid, "distance", distance,\
                  "at txTime", temp_node.packet.txTime, "arriveTime", temp_node.packet.arriveTime)

# sdfsf
# main discrete event loop, runs for each node
# a global list of packet being processed at the gateway
# is maintained
#
def transmit(env, node):
    #broadcast flooding message over the air
    #yield env.timeout(0)
    sensitivity = sensi[node.packet.sf - 7, [125, 250, 500].index(node.packet.bw) + 1]

    for rx_node in nodes:
        if(rx_node.radio_mode is 'rx'):
            node.packet.txTime = env.now
            distance = np.sqrt((node.x - rx_node.x) * (node.x - rx_node.x) + (node.y - rx_node.y) * (node.y - rx_node.y))
            Lpl = Lpld0 + 10 * gamma * math.log10(distance / d0)
            print("Lpl:", Lpl)
            Prx = rx_node.packet.txpow - GL - Lpl
            if Prx < sensitivity:
                print("node ", node.nodeid, " OUT OF range transmission of node ", rx_node.nodeid)
            else:
                node.rssi = Prx
                node.packet.arriveTime = node.packet.txTime + distance / c  # plus propagation time
                if (checkcollision(node.packet) == 1):
                    print("COLLIDED")
                #     node.packet.collided = 1
                else:
                    print("NOT COLLIDED")
                #     node.packet.collided = 0
                rx_node.rxlist.append(node)
                # check collision
                print("node ", node.nodeid, " IN range transmission of node ", rx_node.nodeid, "distance", distance, \
                      "at txTime", node.packet.txTime, "arriveTime", node.packet.arriveTime)

    #yield env.timeout(node.packet.rectime)

    #print("remove packet")
    #
    # if (node in packetsInNetwork):
    #     packetsInNetwork.remove(node)
#
# "main" program
#
def reset():
    for node in nodes:
        node.overhearList.clear()
        node.rxlist.clear()
        if node.nodeid == 0:
            node.parentId = None
            node.rank = 0  # init rank as -1
            node.radio_mode = 'tx'
        else:
            node.parentId = None
            node.rank = -1  # init rank as -1
            node.radio_mode = 'rx'
            global nrNodes
            for i in range(0,nrNodes):
                node.rssi[i] = 0
                node.arriveTime[i] = 0
                node.collided[i] = 0
        node.action=env.process(operate(node.env,node))

# get arguments
if len(sys.argv) >= 3:
    nrNodes = int(sys.argv[1])
    CT_INSERT_ENABLE = int(sys.argv[2])
else:
    print("usage: python CT_Flooding.py <nodes>  <InsertDelay>")
    exit(-1)

simtime = 1000000#int(sys.argv[4])

full_collision = True
print("Nodes:", nrNodes)
print("Simtime: ", simtime)




# global stuff
#Rnd = random.seed(12345)
nodes = []
packetsInNetwork = []
env = simpy.Environment()


# max distance: 300m in city, 3000 m outside (5 km Utz experiment)
# also more unit-disc like according to Utz
avr_hopcount = 0
avr_max_depth = 0
max_hopcount = 0
nrNodeOutNetwork = 0
nrCollisions = 0
total_hopcount = 0

Ptx = 14    #Power Transmission
gamma = 2.08
d0 = 40.0
var = 0           # variance ignored for now
Lpld0 = 126.5
GL = 0

sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])

titles = ["SIMULATION: Normal Flooding", "SIMULATION: Insert Delay Flooding With Timing Alignment", "SIMULATION: Only Insert Delay Flooding"]
xmax = 1380
ymax = 950

#draw map
plt.ion()
plt.figure()
plt.title(titles[CT_INSERT_ENABLE])
ax = plt.gcf().gca()
plt.pause(1)
# prepare graphics and add sink
if (graphics == 1):
    plt.xlim([0, xmax])
    plt.ylim([0, ymax])
    plt.pause(1)
    plt.draw()
    plt.show()
    img = mpimg.imread('E:\Flooding_Experiment\map.png')
    imgplot = plt.imshow(img)


print("******************    PREPARE SIMULATION    **********************")
for i in range(0,nrNodes):
    if i == 0:
        node = myNode(i, 'tx', 20, map[0][i], map[1][i], env)
        node.rank = 0
        nodes.append(node)
    else:
        node = myNode(i,'rx',20, map[0][i], map[1][i], env)
        nodes.append(node)

colorlist = ['red', 'cyan', 'green', 'blue', 'darkviolet', 'dodgerblue', 'gold', 'indigo']
# start simulation
print("******************    START SIMULATION    ********************")
for  y in range(0,100):
    env.run(until=simtime + y*simtime)
    print("")
    print("*****************   RESULT - ",y, "  *********************")
    for mynode in nodes:
        print("NODE ID: ", mynode.nodeid, " In mode: ", mynode.radio_mode)
        if mynode.radio_mode is 'sleep':
            print("             RANK: ", mynode.rank, "----Parent_Node: ", mynode.parentId)
            for parentNode in nodes:
                if(parentNode.nodeid == mynode.parentId):
                    ax.plot([mynode.x, parentNode.x], [mynode.y, parentNode.y], colorlist[7], lw=1)
                    ax.text((mynode.x + parentNode.x) / 2, (mynode.y + parentNode.y) / 2 + 10,
                            str(distance(mynode.nodeid, parentNode.nodeid)) + ' m', color="black", fontsize=8)
                    ax.add_artist(plt.Circle((mynode.x, mynode.y), 8, fill=True, color=colorlist[mynode.rank]))
                    break
            if mynode.maxDepth < mynode.rank:
                mynode.maxDepth = mynode.rank
            max_hopcount = max(max_hopcount, mynode.rank)
            total_hopcount = total_hopcount + mynode.rank
        else:
            nrNodeOutNetwork = nrNodeOutNetwork + 1
        print("        IN OVERHEAR LIST: ")
        for pkt in mynode.overhearList:
            print("             PACKET FROM NODE: ", pkt.nodeid, " IN RANK: ", pkt.rank)
        print("--------------------------------------------------")
        #reset()
    print(y)
    # print stats and save into filE
    if (graphics == 1):
        plt.pause(1)
        plt.draw()
        plt.show()
    # this can be done to keep graphics visible
    plt.pause(0.01)
    for j in range(0, len(ax.texts)-30):
        del ax.texts[30]
    for j in range(0, len(ax.lines)):
        del ax.lines[0]
    #plt.pause(1)
    reset()
avr_hopcount= total_hopcount/(nrNodes*100-nrNodeOutNetwork)
for mynode in nodes:
    avr_max_depth = avr_max_depth + mynode.maxDepth
print(titles[CT_INSERT_ENABLE])
print("NUBER OF NODE: ", nrNodes)
print("NUMBER OF NODES OUT NETWORK: ", nrNodeOutNetwork)
print("AVERAGE HOPCOUNT: ", avr_hopcount)
print("AVERAGE MAXIMUM HOPCOUNT: ", avr_max_depth/nrNodes)
print("MAXIMUM HOPCOUNT: ", max_hopcount)
if (graphics == 1):
    plt.pause(5)
    plt.draw()
    plt.show()
    input('Press Enter to continue ...')

