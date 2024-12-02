# -*- coding: utf-8 -*-
"""
Created on Thu Dec 15 15:23:22 2022

@author: LOA
Server To send shot number
read the Ni card and add +1 each time receive  a trig signal 

"""

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication,QLineEdit,QFileDialog
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QHBoxLayout,QLabel,QSpinBox,QCheckBox
import pathlib
import select
import socket as _socket
from  PyQt6.QtCore import QMutex
import time,sys,os
import qdarkstyle
import nidaqmx #https://github.com/ni/nidaqmx-python
import visu
import moteurRSAIFDB
import uuid
import traceback


class SERVERGUI(QWidget) :
    """
    User interface for shooting class : 
    
    """
    
    def __init__(self,parent=None):
        super(SERVERGUI, self).__init__(parent)
        
        self.p = pathlib.Path(__file__)
        self.sepa = os.sep
        pathini = str(self.p.parent ) + self.sepa + 'configTir.ini'
        self.confTir = QtCore.QSettings(pathini,QtCore.QSettings.Format.IniFormat) 
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        
        hostname = _socket.gethostname()
        self.IPAddr = _socket.gethostbyname(hostname)
        
        self.cursor = moteurRSAIFDB.con.cursor()
        self.listRack = moteurRSAIFDB.rEquipmentList()
        self.rackName = []
        for IP in self.listRack:
            self.rackName.append(moteurRSAIFDB.nameEquipment(IP))
        self.listMotor = []
        for IPadress in self.listRack:
            self.listMotor.append(moteurRSAIFDB.listMotorName(IPadress))

        self.setup()
        self.actionButton()
        self.setWindowTitle('Shot number Server ')
        self.icon = str(self.p.parent) + self.sepa +'icons' + self.sepa
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        # start server
        self.ser = SERVER(self)
        self.ser.start()

        # start daq from NI 
        self.daq=NIDAQ(self)
        self.daq.TRIGSHOOT.connect(self.ChangeTrig)
        self.daq.setZero()
        self.daq.start()

        foldername = time.strftime("%Y_%m_%d")  # Save in a new folder with the time as namefile
        filename = 'SauvegardeMot'+time.strftime("%Y_%m_%d")
        print('Backup motor position file created : ' , foldername)

        pathAutoSave = str(self.p.parent)+self.sepa+'SauvPosition'
        
        folder = pathAutoSave + self. sepa + foldername
        print("folder '%s' " %folder)
        if not os.path.isdir(folder):
            os.mkdir(folder)

        self.fichier = folder + self.sepa + filename +'.txt'

    def setup(self):
        
        vbox1 = QVBoxLayout()
        hbox1 = QHBoxLayout()
        label = QLabel('Shoot server ')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox1.addWidget(label)
        vbox1.addLayout(hbox1)

        self.pathBoxMain = QLineEdit(self.confTir.value('TIR'+"/pathMain"))
        self.buttonPathMain = QPushButton('Path : ')
        hbox = QHBoxLayout()
        hbox.addWidget(self.buttonPathMain)
        hbox.addWidget(self.pathBoxMain)
        vbox1.addLayout(hbox)

        hbox0 = QHBoxLayout()
        labelIP = QLabel()
        labelIP.setText('IP:'+self.IPAddr)
        labelPort = QLabel('Port: 5009')
        hbox0.addWidget(labelIP)
        hbox0.addWidget(labelPort)
        vbox1.addLayout(hbox0)
        hbox2 = QHBoxLayout()
        labelNbShoot = QLabel('Next Shoot Number : ')
        self.nbShoot=QSpinBox()
        self.nbShoot.setMaximum(100000)
        self.nbShoot.setValue(int(self.confTir.value('TIR'+"/shootNumber")))
        self.nbShoot.editingFinished.connect(self.nbShootEdit)
        hbox2.addWidget(labelNbShoot)
        hbox2.addWidget(self.nbShoot)  
        vbox1.addLayout(hbox2)
        hbox3 = QHBoxLayout()
        labelNiconter = QLabel('Trig count : ')
        self.NIShoot = QSpinBox()
        self.NIShoot.setReadOnly(True)
        self.NIShoot.setMaximum(100000)
        hbox3.addWidget(labelNiconter)
        hbox3.addWidget(self.NIShoot)
        
        # self.resetButton=QPushButton('shoot')
        # self.resetButton.clicked.connect(self.shootAct)
        # hbox3.addWidget(self.resetButton)
        vbox1.addLayout(hbox3)
        self.old_value = self.nbShoot.value()
        # sav moteurs
        self.vbox = QVBoxLayout()
        hboxRack = QVBoxLayout()
        LabelRack = QLabel('     Rack NAME to save : ')
        hboxRack.addWidget(LabelRack)
        self.box = []
        i = 0 
        for name in self.rackName: # create QCheckbox for each rack
            self.box.append(checkBox(name=str(name), ip=self.listRack[i], parent=self))
            hboxRack.addWidget(self.box[i])
            i+=1

        self.vbox.addLayout(hboxRack)
        self.vCamBox = QVBoxLayout()
        HCamlayoutLabel = QHBoxLayout()
        labelcam = QLabel(' Camera connected :')
        HCamlayoutLabel.addWidget(labelcam)
        self.autoSave = QCheckBox('autoSave')
        HCamlayoutLabel.addWidget(self.autoSave)
        self.vCamBox.addLayout(HCamlayoutLabel)
        vbox1.addLayout(self.vCamBox)
        # self.butt = QPushButton()
        # self.vbox.addWidget(self.butt)
        vbox1.addLayout(self.vbox)
        self.setLayout(vbox1)
       
    def actionButton(self):
        for b in self.box:
            b.stateChanged.connect(self.clik)

        # self.butt.clicked.connect(self.Action)
        self.buttonPathMain.clicked.connect(self.PathButtonChanged)
        self.pathBoxMain.editingFinished.connect(self.pathBoxChanged)

    def allPosition(self,IpAdress):
        listPosi = []
        listNameMotor =[]
        IdEquipt = moteurRSAIFDB.rEquipmentIdNbr(IpAdress)
        for NoMotor in range (1,15):
            NoMod  = moteurRSAIFDB.getSlotNumber(NoMotor)
            NoAxis = moteurRSAIFDB.getAxisNumber(NoMotor)
            PkIdTbBoc = moteurRSAIFDB.readPkModBim2BOC(self.cursor,IdEquipt, NoMod, NoAxis, FlgReadWrite=1)
            pos = moteurRSAIFDB.getValueWhere1ConditionAND(self.cursor,"TbBim2BOC_1Axis_R", "PosAxis", "PkId", str(PkIdTbBoc))
            step = moteurRSAIFDB.rStepperParameter(self.cursor,PkIdTbBoc, NoMotor,1106)
            listPosi.append(pos*step)
            name = moteurRSAIFDB.rStepperParameter(self.cursor,PkIdTbBoc,NoMotor,2)
            listNameMotor.append(name)
            #print('list posi',listPosi)
        return listPosi,listNameMotor
    
    def clik(self):
        print('click')
        sender = QtCore.QObject.sender(self) 
        print(str(sender.objectName()))
    
    def Action(self):
        foldername = time.strftime("%Y_%m_%d")  # Save in a new folder with the time as namefile
        pathMain = self.pathBoxMain.text()
        folder = pathMain +'/' + foldername 
        
        if not os.path.isdir(folder):
                os.mkdir(folder)
        folder = folder +'/'+ 'SaveMotors'
        if not os.path.isdir(folder):
            os.mkdir(folder)

        filename = 'saveMotorFile'
        
        self.fichier = folder + self.sepa + filename + '.txt'
        self.file = open(self.fichier, "a")
        date = time.strftime("%Y/%m/%d @ %H:%M:%S")
        self.file.write('Shoot number : '+str(self.old_value) +' done the '+ date + "\n")
        self.file.write("Position Motors :" + "\n")
        for b in self.box:
            if b.isChecked():
                listPosi , listNameMotor = self.allPosition(b.ip)
                i = 0
                #print(listPosi,listNameMotor)
                self.file.write('Rack: ' + moteurRSAIFDB.nameEquipment(b.ip) + "  " + str(b.ip)+ "\n" )
                for mot in listNameMotor:
                    self.file.write(str(mot) + ' : ' + str(listPosi[i]) + "\n")
                    i = i+1
            self.file.write(' '+ "\n") 
        self.file.write(''+ "\n")      
        self.file.close()


    def ChangeTrig(self,trigShot):
        print('receive new trig')
        self.NIShoot.setValue(trigShot)
        self.old_value = self.nbShoot.value()  # self.old_value numero du tir en cours
        # on envoi a la camera old_value c'est a dire le tir en cour (le trig arrive 100ms avant le tir et la camera mais du tps a lire)
        self.nbShoot.setValue(int(self.old_value+1)) # le tri a eu lieu  on +1 le tir 
        self.confTir.setValue('TIR'+"/shootNumber",int(self.old_value+1))

        # save motor postion 
        foldername = time.strftime("%Y_%m_%d")  # Save in a new folder with the time as namefile
        filename = 'SauvegardeMot'+time.strftime("%Y_%m_%d")
        print('Backup motor position file created : ' , foldername)
        pathAutoSave = str(self.p.parent)+self.sepa+'SauvPosition'
        folder = pathAutoSave+self.sepa+foldername
        print("folder '%s' " %folder)
        if not os.path.isdir(folder):
            os.mkdir(folder)
            
        self.fichier = folder + self.sepa + filename + '.txt'
        self.file = open(self.fichier, "a")
        date = time.strftime("%Y/%m/%d @ %H:%M:%S")
        self.file.write('Shoot number : '+str(self.old_value) +' done the '+ date + "\n")
        self.file.write("Position Motors :" + "\n")
        for b in self.box:
            if b.isChecked():
                listPosi , listNameMotor = self.allPosition(b.ip)
                i = 0
                self.file.write('Rack: ' + moteurRSAIFDB.nameEquipment(b.ip) + "  " + str(b.ip)+ "\n" )
                for mot in listNameMotor:
                    self.file.write(str(mot) + ' : ' + str(listPosi[i]) + "\n")
                    i = i+1

            self.file.write(' '+ "\n") 
        self.file.write(''+ "\n")      
        self.file.close()
        
    def PathButtonChanged(self):
        self.pathMain = str(QFileDialog.getExistingDirectory( ))
        self.pathBoxMain.setText(self.pathMain)
        
    def pathBoxChanged(self):
        self.confTir.setValue(self.pathMain)

    def nbShootEdit(self):
        self.old_value = self.nbShoot.value()
        self.confTir.setValue('TIR'+"/shootNumber",int(self.old_value+1))

    # def shootAct(self):
    #     print('shoot')
    #     self.ChangeTrig(1)

    def closeEvent(self, event):
        """ when closing the window
        """
        self.ser.stopThread()
        moteurRSAIFDB.closeConnection()
        #self.daq.stopThread()
        time.sleep(2)
        event.accept()


class SERVER(QtCore.QThread):
    '''Server class with multi clients

    '''
#    newDataRun=QtCore.Signal(object)
    def __init__(self,parent=None):
        
        super(SERVER, self).__init__(parent)
        self.parent = parent
        self.serverHost = _socket.gethostname()
        self.serverPort = 5009
        self.clientList = dict()
        self.client_widget = {}
        self.serversocket= _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)      # create socket
        try :
            self.serversocket.bind((self.serverHost,self.serverPort))
            self.isConnected = True
            print('server shot ready')
        except :
            print('error connection server')
            self.isConnected = False
        
        self.listClient = []
        self.clientsConnectedSocket = []
        self.clients_ids = []
    
    
    def run(self): #run
        print('start lisenning')
        
        try: 
            while self.isConnected :
                print('thread server en coyrs')
                self.serversocket.listen(20)
                client_socket, client_adress = self.serversocket.accept()
                client_thread = CLIENTTHREAD(client_socket,client_adress,parent=self)
                client_thread.start()
                client_thread.signalClientThread.connect(self.signalFromClient)
                self.listClient.append(client_thread)
        except Exception as e: 
            print('exception server',e)
            # print('error connection')
            
    def signalFromClient(self,sig):
        client_id = sig[0]
        client_adresse = sig[1]
        nameVisu = sig[2]
        if client_adresse == 0:
            #print('del',client_id)
            del self.clientList[client_id]
            if client_id in self.client_widget:
                label, ckeckbox, Hcam, pathBox, buttonPath = self.client_widget.pop(client_id) # pop retire et retourne la valuer
                label.deleteLater()
                ckeckbox.deleteLater()
                Hcam.deleteLater()
                pathBox.deleteLater()
                buttonPath.deleteLater()       
        else:
            self.clientList[client_id] = client_adresse 
            Hcam = QHBoxLayout()
            label = QLabel(nameVisu)
            foldername = time.strftime("%Y_%m_%d")  # Save in a new folder with the time as namefile
            pathMain = self.parent.pathBoxMain.text()
            folder = pathMain +'/' + foldername 
            if not os.path.isdir(folder):
                os.mkdir(folder)
            folder = folder +'/'+ nameVisu 
            if not os.path.isdir(folder):
                os.mkdir(folder)
            pathBox = QLineEdit(folder)
            buttonPath = QPushButton('Path : ')
            buttonPath.clicked.connect(lambda: self.PathChanged(buttonPath,pathBox))
            
            ckeckbox = QCheckBox('select')
            ckeckbox.setChecked(True)
            self.client_widget[client_id] = (label, ckeckbox, Hcam, pathBox, buttonPath)
            Hcam.addWidget(label)
            Hcam.addWidget(buttonPath)
            Hcam.addWidget(pathBox)
            Hcam.addWidget(ckeckbox)
            self.parent.vCamBox.addLayout(Hcam)
            print('new client: ', self.clientList, nameVisu)
        
    def pathTextChanged(self,button):
        pathAutoSave = self.butt.text()
        
    def PathChanged(self,button,pathBox):
        pathAutoSave = str(QFileDialog.getExistingDirectory( ))
        pathBox.setText(pathAutoSave)
           
    def stopThread(self):
        self.isConnected = False
        print('clossing server')
        time.sleep(0.1)
        for client in self.listClient:
            client.stopThread()
        self.serversocket.close()  
        time.sleep(0.1)                           
        print('stop server')
        time.sleep(0.1)
        #self.terminate() 


class CLIENTTHREAD(QtCore.QThread):
    '''client class 
    '''
    signalClientThread = QtCore.pyqtSignal(object)
    signalUpdate = QtCore.pyqtSignal(object)

    def __init__(self,client_socket,client_adresse,parent=None):
        super(CLIENTTHREAD, self).__init__(parent)
        self.client_socket = client_socket
        #self.client_socket.settimeout(3)
        self.client_adresse = client_adresse
        self.parent = parent
        self.client_id = str(uuid.uuid4())
        self.stop = False 
        #self.parent.parent.signalServer.connect(self.updateConf)
        self.mutex = QMutex()
        
    def run(self):
        print('start new thread client')
        try : 
            while True:
                if self.stop is True:
                    break
                try:
                    data = self.client_socket.recv(1024)
                    msgReceived = data.decode()
                    if not msgReceived:
                        #print('pas de message')
                        self.signalClientThread.emit([self.client_id,0,0])
                        break
                    else: 
                            try :
                                msgsplit = msgReceived.split(',')
                                msgsplit = [msg.strip() for msg in msgsplit]
                               
                                if len(msgsplit) == 1 :
                                    msgReceived = msgsplit[0]
                                    if msgReceived == 'numberShoot?':
                        
                                        number = str(self.parent.parent.old_value) # send the shoot nuber not the n+1
                                            # print('server number',number)
                                        self.client_socket.send(number.encode())
                    
                                    elif msgReceived == 'idShoot?':
                                        numberId = str(self.parent.parent.old_value)  +"@"+self.parent.date2 # send the shoot nuber not the n+1
                                        self.client_socket.send(number.encode())
                                    
                                    elif msgReceived == 'path':
                                        (label,ckeckbox,Hcam,pathBox,buttonPath)  = self.parent.client_widget[self.client_id] 
                                        pathSend = str(pathBox.text())
                                        number = str(self.parent.parent.old_value) # send the shoot nuber not the n+1
                                        
                                        if (ckeckbox.isChecked() is True) and (self.parent.parent.autoSave.isChecked() is True) : # camera selected and autosave selected
                                            autosave = True
                                        else:
                                            autosave = False
                                        
                                        cmd = "%s, %s, %s" %(number,pathSend,autosave)
                                        self.client_socket.send(cmd.encode())

                                elif len(msgsplit) == 2:
                                    cmd = msgsplit[0]
                                    value = msgsplit[1]
                                    if cmd == 'nameVisu' :
                                        self.nameVisu = value
                                        cmd = 'ok' 
                                        self.client_socket.sendall(cmd.encode())
                                        print('connection to ', self.nameVisu ,'@',self.client_adresse)
                                        self.signalClientThread.emit([self.client_id,self.client_adresse,self.nameVisu])
                            except:
                                print('error')
                                sendmsg = 'error'
                                traceback.print_exc()
                                self.client_socket.sendall(sendmsg.encode())

                except ConnectionResetError:
                    print('deconnection du client')
                    self.client_socket.close()
                    self.signalClientThread.emit([self.client_id,0,0])
                    break

        except Exception as e: 
            print('exception server',e)
            self.client_socket.close()
            self.signalClientThread.emit([self.client_id,0,0])

    def stopThread(self):
        self.stop = True 


class NIDAQ(QtCore.QThread)  : 
    TRIGSHOOT = QtCore.pyqtSignal(int)

    def __init__(self,parent=None):
        super(NIDAQ, self).__init__(parent)
        self.parent = parent
        self.stop = False
       
    def run(self):
        a=0
        with nidaqmx.Task() as task:
            task.ci_channels.add_ci_count_edges_chan("Dev1/ctr0", edge=nidaqmx.constants.Edge.FALLING)
            task.start()
            while True:
                if self.stop is True:
                    break
                else:
                    time.sleep(0.1)
                    b = task.read()
                    # print('daq nb',b)
                    if b!=a:
                        a = b
                        self.TRIGSHOOT.emit(a)

    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        self.terminate()   

    def setZero(self):
    #   with nidaqmx.Task() as task:
        print('set daq to zero')

class checkBox(QCheckBox):
    # homemade QCheckBox

    def __init__(self,name='test',ip='', parent=None):
        super(checkBox, self).__init__()
        self.parent = parent 
        self.ip = ip
        self.name = name
        self.setText(self.name+' ( '+ self.ip+ ')')
        self.setObjectName(self.ip)           
                    
if __name__ =='__main__':
    appli = QApplication(sys.argv)
    e = SERVERGUI()
    e.show()
    appli.exec_()