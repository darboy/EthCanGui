import CanFrame_pb2
import socket
import struct
import time
import os
import sys
import CanData as can

class receiveBase(object):
    def __init__(self):
        self.data_que = []
    def pushData(self, tx_data):
        if isinstance(tx_data, can.txCanData):
            self.data_que.append(tx_data)
        else:
            print("push data type error %s %s" % (type(tx_data),type(can.txCanData)))
        self.data_que.append(tx_data)
    def read(self):
        pass

class receiveByUdp(receiveBase):
    def __init__(self):
        super(receiveByUdp, self).__init__()
        self.so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.so.settimeout(2)
        self.launchEthCanTool()
        self.msgdict = {}
        self.framerate = (0, 0)
        self.remoteaddr = ""
        self.data = ""
        self.launchEthCanTool()
        self.queryForFrame(50)

    def launchEthCanTool(self):
        self.so.sendto(struct.pack('<2I', 0x1016, 0xffffffff), ('192.168.192.4', 15003))
        try:
            (self.data, self.remoteaddr) = self.so.recvfrom(1024)
        except socket.timeout:
            pass
    
    def queryForFrame(self, num):
        fullMsg = struct.pack('<2I', 0x1019, num)
        self.so.sendto(fullMsg, ('192.168.192.4', 15003))

    def read(self):
        try:
            (self.data, self.remoteaddr) = self.so.recvfrom(1024)
        except socket.timeout:
            print('timeout')
            self.launchEthCanTool()
        (msgId, pbdata) = struct.unpack('<I' + str(len(self.data) - 4) + 's', self.data)
        frame = CanFrame_pb2.CanFrame()
        update = False
        if(0x00001019 == msgId):
            try:
                frame.ParseFromString(pbdata)
            except:
                print('pbdata parse error')
                print(self.data)
                os.system('pause')
            self.msgdict[frame.ID] = frame
            update = True
        elif 0x00001041 == msgId:
            self.framerate = struct.unpack('<2I', pbdata)
        if(update):
            dirc = ''
            if(self.msgdict[frame.ID].Direction == 1):
                dirc = 'TX'
            else:
                dirc = 'RX'
            tmps = '0x%04X\t%d\t%d\t%s\t%d\t{ ' % (
                self.msgdict[frame.ID].ID, self.msgdict[frame.ID].Channel, self.msgdict[frame.ID].DLC, dirc, self.msgdict[frame.ID].Timestamp)
            for i in range(0, self.msgdict[frame.ID].DLC):
                tmps += ('0x%02X ' % self.msgdict[frame.ID].Data[i])
            tmps += '}\n'
            sys.stdout.write(tmps)

if __name__ == "__main__":
    test = receiveByUdp()
    while True:
        test.read()