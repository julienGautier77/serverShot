import time,os
import pathlib
import shutil


## sauvegarde des fichiers init
date=time.strftime("%Y_%m_%d_%H_%M_%S")

p = pathlib.Path(__file__)
sepa=os.sep
fichierIni=str(p.parent )+sepa+'confCameras.ini'
pathfichierIniSauv=str(p.parent )+sepa+'Sauvegarde'
pathfichierIniSauv=pathfichierIniSauv+sepa+'confCamera_'+date+'.ini'
shutil.copyfile(fichierIni,pathfichierIniSauv)

