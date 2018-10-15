#!/usr/bin/python
path = "E:\\IOT_LAB\\CT_experiment_result\\"
print(path+"ct_log.txt")
file = open(path+"ct_log.txt", "r")

result_file = open(path+"result.txt", "w")
rssi1 = 0
rssi2 = 0
node1 = 0
node2 = 0
tp = -1
t_offset = -1
index = 0

#ready_info = False
for lines in file.readlines():
    line = lines.replace(" ", "")
    post_line = line.replace("--",",")
    if(post_line.find('RX',)!=-1):

        print(post_line)
        part = post_line.split(',')
        index = int(part[2].split(':')[1])
        if index == 6:
            tp = int(part[3].split(':')[1])
            t_offset = int(part[4].split(':')[1])
        if index == 0:
            newline = "TP:" + str(tp) + "  --- tOffset" + str(t_offset) + ": NODE_1: " + str(node1) +" (" + str(rssi1/5) + ") " +"   NODE_2:"+ str(node2) +" (" + str(rssi2/5) + ") "+"\n"
            result_file.write(newline)
            result_file.write("\n")
            node1 = 0
            node2 = 0
            rssi1 = 0
            rssi2 = 0
            tp = 0
            t_offset = 0
        if index > 10:
            if int(part[1].split(':')[1]) == 1:
                node1 = node1 + 1
            if int(part[1].split(':')[1]) == 2:
                node2 = node2 + 1
    if index > 0 and index < 6:
        if (post_line.find('RSSI:', ) != -1):
            rssi_line = post_line.replace("dBm", "")
            rssi_part = rssi_line.split(':')
            rssi1 = rssi1 + int(rssi_part[1])
    if index > 5 and index < 11:
        if (post_line.find('RSSI:', ) != -1):
            rssi_line = post_line.replace("dBm", "")
            rssi_part = rssi_line.split(':')
            rssi2 = rssi2 + int(rssi_part[1])