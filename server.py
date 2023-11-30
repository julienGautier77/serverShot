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
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QHBoxLayout,QLabel,QSpinBox
import pathlib
import select
import socket as _socket
import time,sys,os
import qdarkstyle
import nidaqmx #https://github.com/ni/nidaqmx-python
import visu

class SERVERGUI(QWidget) :
    """
    User interface for shooting class : 
    
    """
    
    def __init__(self,parent=None):
        
        super(SERVERGUI, self).__init__(parent)

        p = pathlib.Path(__file__)
        sepa=os.sep
        pathini=str(p.parent )+sepa+'configTir.ini'
        
        self.confTir=QtCore.QSettings(pathini,QtCore.QSettings.Format.IniFormat) 
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        print(self.confTir.value('TIR'+"/shootNumber"))
        hostname = _socket.gethostname()
        self.IPAddr = _socket.gethostbyname(hostname)
        
        self.setup()
        self.setWindowTitle('Shot number Server ')
        self.icon=str(p.parent) + sepa+'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.ser=SERVER(self)
        self.ser.start()
        self.daq=NIDAQ(self)
        self.daq.TRIGSHOOT.connect(self.ChangeTrig)
        self.daq.setZero()
        self.daq.start()


        foldername=time.strftime("%Y_%m_%d")  # Save in a new folder with the time as namefile
        filename='SauvegardeMot'+time.strftime("%Y_%m_%d")
        print('Backup motor position file created : ' , foldername)

        pathAutoSave=str(p.parent)+sepa+'SauvPosition'
        
        folder=pathAutoSave+sepa+foldername
        print("folder '%s' " %folder)
        if not os.path.isdir(folder):
    
            os.mkdir(folder)
            
        self.fichier=folder+sepa+filename+'.txt'

        
    def setup(self):
        
        vbox1=QVBoxLayout()
        
        hbox1=QHBoxLayout()
        label=QLabel('Number Shoot server ')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox1.addWidget(label)
        vbox1.addLayout(hbox1)
        hbox0=QHBoxLayout()
        labelIP=QLabel()
        labelIP.setText('IP:'+self.IPAddr)
        labelPort=QLabel('Port: 5009')
        hbox0.addWidget(labelIP)
        hbox0.addWidget(labelPort)
        vbox1.addLayout(hbox0)
        hbox2=QHBoxLayout()
        labelNbShoot=QLabel('Next Shoot Number : ')
        self.nbShoot=QSpinBox()
        self.nbShoot.setMaximum(100000)
        self.nbShoot.setValue(int(self.confTir.value('TIR'+"/shootNumber")))
        self.nbShoot.editingFinished.connect(self.nbShootEdit)
        hbox2.addWidget(labelNbShoot)
        hbox2.addWidget(self.nbShoot)
        
        vbox1.addLayout(hbox2)
        
        hbox3=QHBoxLayout()
        labelNiconter=QLabel('Trig count : ')
        self.NIShoot=QSpinBox()
        self.NIShoot.setMaximum(100000)
        hbox3.addWidget(labelNiconter)
        hbox3.addWidget(self.NIShoot)
        
        # self.resetButton=QPushButton('shoot')
        # self.resetButton.clicked.connect(self.shootAct)
        # hbox3.addWidget(self.resetButton)
        vbox1.addLayout(hbox3)

        self.old_value=self.nbShoot.value()
        
        self.setLayout(vbox1)
       # self.setGeometry(QRect(107, 75, 250, 250))


    def ChangeTrig(self,trigShot):
        self.NIShoot.setValue(trigShot)
        self.old_value=self.nbShoot.value()  # self.old_value numero du tir en cours
        # on envoi a la camera old_value c'est a dire le tir en cour (le trig arrive 100ms avant le tir et la camera mais du tps a lire)

        self.nbShoot.setValue(int(self.old_value+1)) # le tri a eu lieu  on +1 le tir 
        self.confTir.setValue('TIR'+"/shootNumber",int(self.old_value+1))
        #save motor postion
        # 
        self.file = open(self.fichier, "a")
        date=time.strftime("%Y/%m/%d @ %H:%M:%S")
        # print("date main",date)
        self.date2=time.strftime("%Y%m%d%H%M%S")
        self.file.write('Shoot number : '+str(self.old_value) +' done the '+date+ "\n")
        self.file.write(''+ "\n")
        # to do ... save motor position with data rsai data base
        self.file.close()

    def nbShootEdit(self):
        self.old_value=self.nbShoot.value()

    # def shootAct(self):
    #     print('shoot')
    #     self.ChangeTrig(1)

    def closeEvent(self, event):
        """ when closing the window
        """
        self.daq.stopThread()
        self.ser.stopThread()
        event.accept()


class SERVER(QtCore.QThread):
    '''Server class with multi clients

    '''
#    newDataRun=QtCore.Signal(object)
    def __init__(self,parent=None):
        
        super(SERVER, self).__init__(parent)
        self.parent=parent
        self.serverHost = ''
        self.serverPort = 5009
        
        self.serversocket= _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)      # create socket
        try :
            self.serversocket.bind((self.serverHost,self.serverPort))
            self.isConnected = True
            print('server shot ready')
        except :
            print('error connection server')
            self.isConnected = False
        
        self.clientsConnectedSocket = []
    
    def stopConnexion(self):
        self.isConnected = False
        time.sleep(1)
        self.serversocket.close()                             # close socket
        print('stop server shot')
    
    def run(self):#run
        print('start lisenning')
        
        while self.isConnected==True:
#            number=str(self.parent.nbShoot.value())
#                        
#            print('server number',number)
            self.serversocket.listen(5)
            # On va vérifier que de nouveaux clients ne demandent pas à se connecter
            connexions_demandees, wlist, xlist = select.select([self.serversocket],[], [], 0.05)
           
            for connexion in connexions_demandees:
                # on accepte les connexions
                connexion_avec_client, infos_connexion = connexion.accept()
                # On ajoute le socket connecté à la liste des clients
                
                self.clientsConnectedSocket.append(connexion_avec_client)
            
            # Maintenant, on écoute la liste des clients connectés
            # Les clients renvoyés par select sont ceux devant être lus (recv)
            # On attend là encore 50ms maximum
            # On enferme l'appel à select.select dans un bloc try
            # En effet, si la liste de clients connectés est vide, une exception
            # Peut être levée
            
            clientsToRead = []
            try:
                clientsToRead, wlist, xlist = select.select(self.clientsConnectedSocket,[], [], 0.05)
            except select.error:
                pass
            else:
                # On parcourt la liste des clients à lire
                for client in clientsToRead:
                    # Client est de type socket
                    try:
                        msgReceived= client.recv(1024)
                        msgReceived=msgReceived.decode()
                    except:
                        msgReceived=''
                    if msgReceived=='close server':
                        print('close server')
                        for client in self.clientsConnectedSocket:
                            client.close()
                        time.sleep(0.2) 
                        self.serversocket.Client.Disconnect(True)
                        self.serversocket.close()
                        self.isConnected=False
                        
                        
                    elif msgReceived=='numberShoot?':
                        
                        number=str(self.parent.old_value) # send the shoot nuber not the n+1
                        
                        print('server number',number)
                        client.sendall(number.encode())
                    
                    elif msgReceived=='idShoot?':
                        
                        numberId=str(self.parent.old_value)  +"@"+self.parent.date2 # send the shoot nuber not the n+1
                        
                        
                        print('shoot id ',numberId)
                        client.sendall(number.encode())

                    elif msgReceived  : 
                        
                        print('message received: ',msgReceived)
                        messageSend='mess received:  '+msgReceived
                        
                        client.sendall(messageSend.encode())

    def stopThread(self):
        self.isConnected=False
        time.sleep(0.2)
        self.stopConnexion()
        time.sleep(0.1)
        self.terminate() 
                        
class NIDAQ(QtCore.QThread)  : 
    TRIGSHOOT=QtCore.pyqtSignal(int)
    def __init__(self,parent=None):
        super(NIDAQ, self).__init__(parent)
        self.parent=parent
        self.stop=False

       
    def run(self):
        a=0
        with nidaqmx.Task() as task:
            task.ci_channels.add_ci_count_edges_chan("Dev1/ctr0", edge=nidaqmx.constants.Edge.FALLING)
            task.start()
            while True:
                if self.stop==True:
                    break
                else:
                    time.sleep(0.1)
                    b=task.read()
                    # print('daq nb',b)
                    if b!=a:
                        a=b
                        self.TRIGSHOOT.emit(a)

    def stopThread(self):
        self.stop=True
        time.sleep(0.1)
        self.terminate()   

    def setZero(self):
    #   with nidaqmx.Task() as task:
        print('set daq to zero')
            


                 
                        
if __name__ =='__main__':
    appli=QApplication(sys.argv)
    e=SERVERGUI()
    e.show()
    appli.exec_()