#!/usr/bin/python

import random
import numpy as np
import math
import sys
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.image as mpimg
#        0    1    2    3    4    5    6    7    8    9    10  11   12  13    14   15   16    17   18    19  20    21  22   23   24   25   26   27   28   29
map = [[663, 785, 802, 631, 635, 525, 759, 425, 332, 651, 117, 80, 1085, 432, 836, 288, 791, 1100, 927, 197, 880, 281, 630, 259, 962, 529, 952, 736, 443, 746],
               [836, 534, 712, 647, 229, 389, 82, 594, 323, 489, 442, 634, 337, 699, 178, 618, 369, 457, 88, 282, 310, 488,
                360, 699, 201, 566, 561, 214, 271, 1]]

def distance(id1,id2):
    scale = 0.68
    return int(np.sqrt((nodes[id1].x - nodes[id2].x) * (nodes[id1].x - nodes[id2].x) + (nodes[id1].y - nodes[id2].y) * (nodes[id1].y - nodes[id2].y))*scale)

class myNode():
    def __init__(self, nodeid):
        self.nodeid = nodeid
        self.depth = []
        self.parent = []
        self.isInNetwork = []
        self.x = 0
        self.y = 0
        self.max_depth =0
class Index(object):
    ind = 0

    def pause(self, event):
        plt.pause(10)

    def play(self, event):
        plt.show()


#main
# get arguments
if len(sys.argv) >= 3:
    show_index = int(sys.argv[1])
    case = int(sys.argv[2])
    type = int(sys.argv[3])
else:
    print("usage: python process_experiment_flooding_log.py <index[-1 or 0:99]>  <case[0:3]> <type[0:2]>")
    exit(-1)

graphics = 1
xmax = 1380
ymax = 950

nodes = []
#result
avr_depth = 0
max_depth = 0
avr_max_depth = 0
nr_out = 0

nrNode = [10, 15, 20, 30]
titles = [["10 Nodes - NormalFlooding",\
         "10 Nodes - Allignment Insert Flooding",\
         "10 Nodes - Only Insert Flooding"],\
        ["15 Nodes - Normal Flooding",\
         "15 Nodes - Allignment Insert Flooding",\
         "15 Nodes - Only Insert Flooding"],\
        ["20 Nodes - Normal Flooding",\
         "20 Nodes - Allignment Insert Flooding",\
         "20 Nodes - Only Insert Flooding"],\
        ["30 Nodes - Normal Flooding",\
         "30 Nodes - Allignment Insert Flooding",\
         "30 Nodes - Only Insert Flooding"]]

path = [["E:\\Flooding_Experiment\\NewLog\\10Nodes_0NormalFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\10Nodes_1AllignmentInsertFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\10Nodes_2OnlyInsertFlooding\\"],\
        ["E:\\Flooding_Experiment\\NewLog\\15Nodes_0NormalFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\15Nodes_1AllignmentInsertFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\15Nodes_2OnlyInsertFlooding\\"],\
        ["E:\\Flooding_Experiment\\NewLog\\20Nodes_0NormalFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\20Nodes_1AllignmentInsertFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\20Nodes_2OnlyInsertFlooding\\"],\
        ["E:\\Flooding_Experiment\\NewLog\\30Nodes_0NormalFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\30Nodes_1AllignmentInsertFlooding\\",\
         "E:\\Flooding_Experiment\\NewLog\\30Nodes_2OnlyInsertFlooding\\"]]
file = []
for i in range(1,nrNode[case]):
    print(path[case][type]+str(i)+".txt")
    file.append(open(path[case][type]+str(i)+".txt", "r", encoding="utf-8-sig"))


#draw map
plt.ion()
plt.figure()
plt.title(titles[case][type])
ax = plt.gcf().gca()
plt.pause(1)



#prepare show
if (graphics == 1):
    plt.xlim([0, xmax])
    plt.ylim([0, ymax])
    plt.pause(1)
    plt.draw()
    plt.show()
    img = mpimg.imread('E:\Flooding_Experiment\map.png')
    imgplot = plt.imshow(img)
callback = Index()
axprev = plt.axes([0.85, 0.5, 0.1, 0.045])
axnext = plt.axes([0.85, 0.6, 0.1, 0.045])
bnext = Button(axnext, 'Pause')
bnext.on_clicked(callback.pause)
bprev = Button(axprev, 'index')

#draw node on to map
for i in range(0,nrNode[case]):
    if i == 0: #or i == 1 or i == 2:
        node = myNode(i)
        for j in range(0,100):
            node.depth.append(0)
            node.isInNetwork.append(True)
            node.parent.append(0)
        node.x = map[0][i]
        node.y = map[1][i]
        nodes.append(node)
        plt.pause(1)
        ax.add_artist(plt.Circle((node.x, node.y), 8, fill=True, color='red'))
        ax.text(node.x - 8, node.y + 12, str(node.nodeid), color="red", fontsize=10)
    else:
        node = myNode(i)
        for j in range(0,100):
            node.depth.append(-1)
            node.isInNetwork.append(False)
            node.parent.append(-1)
        node.x = map[0][i]
        node.y = map[1][i]
        nodes.append(node)
        ax.add_artist(plt.Circle((node.x, node.y), 8, fill=True, color='blue'))
        ax.text(node.x - 8, node.y + 12, str(node.nodeid), color="red", fontsize=10)

#handle data
plt.pause(4)
for i in range(0,nrNode[case]-1):
    index = -1
    #ready_info = False
    for lines in file[i].readlines():
        line = lines.replace(" ", "")
        if(line.find('NO:',)!=-1):
            seq = line.split(':')
            index = int(seq[1])
            if index > 99:
                break

        if(line.find('Parent',)!=-1):
            part = line.split(',')
            #print(part)
            seq1 = part[0].split(':')
            nodes[i+1].parent[index] = int(seq1[1])
            seq2 = part[2].split(':')
            nodes[i+1].depth[index] = int(seq2[1])
            if nodes[i+1].depth[index]>7:
                print("bat thuong")
                print(lines)
                print(i)
                print(nodes[i+1].depth[index])
            nodes[i+1].isInNetwork[index]= True
            if nodes[i+1].depth[index]>nodes[i + 1].max_depth:
                nodes[i + 1].max_depth = nodes[i+1].depth[index]

colorlist = ['red', 'cyan', 'green', 'blue', 'darkviolet', 'dodgerblue', 'gold', 'indigo']
max_depth_times = 0
if show_index != -1 and show_index <100 and show_index > -1:
    print(show_index)
    bprev.label.set_text("#No: " + str(show_index))
    for mynode in nodes:
        if (mynode.isInNetwork[show_index]):
            for parentNode in nodes:
                if (parentNode.nodeid == mynode.parent[show_index]):
                    ax.plot([mynode.x, parentNode.x], [mynode.y, parentNode.y], colorlist[7], lw=1)  ## display link
                    # text.append(plt.text((mynode.x +parentNode.x)/2, (mynode.y +parentNode.y)/2, str(distance(mynode.nodeid, parentNode.nodeid)) + ' m', color="red", fontsize=8)) ## display distance
                    if mynode.nodeid != 0:
                        ax.text((mynode.x + parentNode.x) / 2, (mynode.y + parentNode.y) / 2 + 10,
                                str(distance(mynode.nodeid, parentNode.nodeid)) + ' m', color="black", fontsize=10)
                    ax.add_artist(plt.Circle((mynode.x, mynode.y), 8, fill=True, color=colorlist[
                        mynode.depth[show_index]]))  ## change color of node depends on its depth
                    break
        else:
            print('Node: ', mynode.nodeid, ' out of network')
    plt.pause(1000)

else:
    for i in range(0,100):

        bprev.label.set_text("#No: " + str(i))
        print(i)
        for mynode in nodes:
            if(mynode.isInNetwork[i]):
                for parentNode in nodes:
                    if (parentNode.nodeid == mynode.parent[i]):
                        ax.plot([mynode.x , parentNode.x], [mynode.y , parentNode.y], colorlist[7], lw=1)  ## display link
                        #text.append(plt.text((mynode.x +parentNode.x)/2, (mynode.y +parentNode.y)/2, str(distance(mynode.nodeid, parentNode.nodeid)) + ' m', color="red", fontsize=8)) ## display distance
                        if mynode.nodeid!=0:
                            ax.text((mynode.x + parentNode.x) / 2, (mynode.y + parentNode.y) / 2 + 10,
                                     str(distance(mynode.nodeid, parentNode.nodeid)) + ' m', color="black", fontsize=10)
                        ax.add_artist(plt.Circle((mynode.x, mynode.y), 8, fill=True, color=colorlist[mynode.depth[i]]))  ## change color of node depends on its depth
                        break
                avr_depth = avr_depth+  mynode.depth[i]
                if max_depth < mynode.depth[i]:
                    max_depth_times = i
                    max_depth = mynode.depth[i]
            else:
                print('Node: ',mynode.nodeid,' out of network')
                nr_out = nr_out +1
        plt.pause(0.01)
        for j in range(0, len(ax.texts)-30):
            del ax.texts[30]
        for j in range(0, len(ax.lines)):
            del ax.lines[0]
if show_index != -1 and show_index <100 and show_index > -1:
    print("")
else:

    for mynode in nodes:
        avr_max_depth = avr_max_depth + mynode.max_depth
        print("NODE: ", mynode.nodeid , "- Maximum Depth:", mynode.max_depth)
    print(titles[case][type])
    print("NUMBER OF NODES OUT NETWORK: ", nr_out)
    print("AVERAGE HOPCOUNT: ", avr_depth/(nrNode[case]*100-nr_out))
    print("AVERAGE MAXIMUM HOPCOUNT: ",avr_max_depth/nrNode[case])
    print("MAXIMUM HOPCOUNT: ", max_depth, "in times: ", max_depth_times)
if (graphics == 1):
    plt.pause(1000)
    plt.draw()
    plt.show()
    input('Press Enter to continue ...')

for i in range(0,30):
    file[i].close();