# -*- coding: UTF-8
"""
Pilotage des controleurs RSAI via les ddl PilmotTango.dll et openMD.dll
python 3.X pyQT6
system 64 bit (at least python MSC v.1900 64 bit (Intel)) 
@author: Gautier julien loa
Created on Tue Jan 4 10:42:10 2018
modified on Tue Feb 27 15:49:32 2018
"""

#%% Imports
import ctypes
import time
import sys
import pathlib,os#logging
try:
    from PyQt6.QtCore import QSettings
except:
    print('erro pyQT6 import)')


#%% DLL

if sys.maxsize <2**32:
    print('you are using a 32 bits version of python use 64 bits or change RSAI dll') 
p = pathlib.Path(__file__)
sepa=os.sep
dll_file = str(p.parent) + sepa+'DLL'+sepa+'PilMotTango.dll'
#modbus_file='DLL/OpenModbus.dll'
try:
    #PilMot=ctypes.windll.PilMotTango # Chargement de la dll PilMotTango et OpenMD .dll
    PilMot = ctypes.windll.LoadLibrary(dll_file)
    #modbus=ctypes.windll.LoadLibrary(modbus_file)
except AttributeError as s:
    print('########################################################')
    print("Error when loading the dll file : %s" % dll_file)
    print("Error : %s" % s)
    print("PilMot() is then a dummy class.")
    print('########################################################')
    class PilMot():
        """ dummy class """
        def rEtatConnexion(i):
            return i
        def Start(i, s):
            return 0
        def rPositionMot(i, j):
            return 10.
        def wCdeMot(i, j, k, l, m):
            return
        def wPositionMot(i, j, k):
            return
        def rEtatMoteur(i, j):
            return 0
        def Stop():
            return 0

#%% ENTREE
# liste adresse IP des modules
IP    = b"10.0.1.30       10.0.1.31       10.0.3.31      " 
IPs_C = ctypes.create_string_buffer(IP, 48) # permet d avoir la liste comme demander dans la dll

configPath=str(p.parent)+sepa+"fichiersConfig"+sepa
print(configPath)
#conf = QSettings(QSettings.IniFormat, QSettings.UserScope, "configMoteur", "configMoteurRSAI")
confRSAI = QSettings(configPath+'configMoteurRSAI.ini', QSettings.Format.IniFormat)




#%% Functions connections RSAI
def startConnexion():
    """ Ouverture d'une connexion avec les racks RSAI """
    print("RSAI initialisation ...")
    argout = 0
    argoutetat = PilMot.rEtatConnexion( ctypes.c_int16(0) ) # numero equipement
    if argoutetat != 3:
        argout = PilMot.Start(ctypes.c_int(3), IPs_C) # nb equipement , liste IP
        if argout == 1 :
            print('RSAI connection : OK RSAI connected @\n', IP)
        else:
            print('RSAI connexion failed')
    return argout

def stopConnexion():
    """ arret des connexions """
    print('RSAI  connexion stopped ')
    PilMot.Stop() # arret de toute les connexion


def testConnection():
    argout = PilMot.rEtatConnexion(ctypes.c_int16(0)) # numero equipement
    if argout == 3:
            print('Test connection OK')
    elif argout == 1:
            print('Already connected at \n', IP)
    else :
        print('Test connexion failed')
    return argout



#%% class MOTORSAI
    
class MOTORRSAI():
    def __init__(self, mot1='',parent=None):
        #super(MOTORNEWPORT, self).__init__()
        self.moteurname=mot1
        try: 
            self.numEsim=ctypes.c_int16(int(confRSAI.value(self.moteurname+'/numESim')))
        except:
            print('configuration file error : motor name or motortype is not correct ')
        try:
            self.numMoteur=ctypes.c_int16(int(confRSAI.value(self.moteurname+'/numMoteur')) )
        except:
            print('configuration file error : motor name or motortype is not correct ')
            # sys.exit()
        date=time.strftime("%Y_%m_%d")
        fileNameLog=str(p.parent)+sepa+'motorLog'+sepa+'logMotor_'+date+'.log'
        # print('filenamelog',fileNameLog)
        # logging.basicConfig(filename=fileNameLog, encoding='utf-8', level=logging.INFO,format='%(asctime)s %(message)s')

    def stopMotor(self): # stop le moteur motor
        """ stopMotor(motor): stop le moteur motor """
        regCde = ctypes.c_uint(8) # 8 commande pour arreter le moteur
        PilMot.wCdeMot( self.numEsim , self.numMoteur, regCde, 0, 0)
        print("Stop")


    def move(self, pos, vitesse=200):
        """
        move(self.moteurname,pos,vitesse): mouvement absolu du moteur (motor) a la position pos avec la vitesse vitesse
        """
        regCde = ctypes.c_uint(2) # commande mvt absolue
        posi   = ctypes.c_int(int(pos))
        vit    = ctypes.c_int( int(vitesse) )
        print(time.strftime("%A %d %B %Y %H:%M:%S"))
        print(self.moteurname, "position before ", self.position(), "(step)")
        PilMot.wCdeMot(self.numEsim , self.numMoteur, regCde, posi, vit)
        print(self.moteurname, "move to", pos, "(step)")
        tx='motor ' +self.moteurname +'  absolute move to ' + str(pos) + ' step  ' + '  position is :  ' + str(self.position())+'step'
        # logging.info(tx)

    def rmove(self, posrelatif, vitesse=200):
        """
        rmove(motor,posrelatif,vitesse): : mouvement absolu du moteur (motor) a la position posrelatif avec la vitesse vitesse
        """
        regCde    = ctypes.c_uint(2) # commande mvt 
        posActuel = self.position()
        print(time.strftime("%A %d %B %Y"))
        print(self.moteurname,"position before ",posActuel,"(step)")
        pos  = int(posActuel+posrelatif)
        posi = ctypes.c_int(pos)
        vit  = ctypes.c_int(int(vitesse))
        PilMot.wCdeMot(self.numEsim , self.numMoteur, regCde, posi, vit)
        print(self.moteurname, "relative move of", posrelatif, "(step)")
        tx='motor ' +self.moteurname +' rmove  of ' + str(posrelatif) + ' step  ' + '  position is :  ' + str(self.position())+'step'

        # logging.info(tx)

    def setzero(self):
        """
        ## setzero(self.moteurname):Set Zero
        """
        regCde=ctypes.c_int(1024) #  commande pour zero le moteur (2^10)

        a=PilMot.wCdeMot(self.numEsim , self.numMoteur,regCde,ctypes.c_int(0),ctypes.c_int(0))
       
        print (self.moteurname,"zero set",a)
        tx='motor '+ self.moteurname + 'set to :  ' + '  '+ str(0)

        # logging.info(tx)
        

#%% Functions ETAT Moteur

    def etatMotor(self):
        """ Etat du moteur (alimentation on/off)
        a verifier
        """
        a=PilMot.rEtatMoteur(self.numEsim , self.numMoteur)
        a=hex(a)
        # print('mot err',a)
        if a=='0x2030' or a=='0x30' : 
            etat='mvt'
        
        elif a=='0x2012' or a=='0x12' or a=='0x92' or a=='0x2082' or a=='0x2092': 
            etat='FDC-'
        elif a=='0x2011' or a=='0x11' or a=='0x91' or a=='0x2081' or a=='0x2091': 
            etat='FDC+'
        elif a=='0x2010' or a=='0x10' : 
            etat='ok'
        elif a=='0x2090' or a=='0x90' : 
            etat='ok'    
        elif a=='0x2090' or a=='0x90' : 
            etat='ok'
        elif a=='0x890' or a=='0x2890' or a=='0x810'or a=='0x880'or a=='0x2880' or a=='0x800' or a=='0x4800': 
            etat='Power off'
        else:
            etat='?'
        return etat

    def position(self):
        """ position (self.moteurname) : donne la postion de motor """
        pos=PilMot.rPositionMot(self.numEsim , self.numMoteur) # lecture position theorique en nb pas
        return pos
 
    
#%% Demarage connexion
        
startConnexion()   

 
#%%
if __name__ == "__main__":
    print("test")
    #startConnexion()


