import sys, os, m8r
import numpy as np
import matplotlib.pyplot as plt


def getData (Dir, File, Header):
    '''Read RSF data from SEGY and Headers and makes it 2 numpy arrays'''
    F = m8r.Input(Dir+os.sep+File)
    TrH = m8r.Input(Dir+os.sep+Header)
    Data = np.array(F)
    TrHead= np.array(TrH)
    return Data, TrHead

def WriteRsf(Array, Dir, Name, Tsample, Rspacing):
    '''Writes numpy array and its mask into optimised rsf file'''
    n1,n2,n3 = np.shape(Array)
    Out      = m8r.Output(Dir+os.sep+Name)
    Mask_Out = m8r.Output(Dir+os.sep+'Mask_'+Name)
    # array gets transposed in rsf
    axis = [{'n':n3,'d':Tsample,'o':0,'l':'Time','u':'s'},
            {'n':n2,'d':Rspacing,'o':0,'l':'Offset','u':'m'},
            {'n':n1,'d':1,'o':0,'l':'Shot','u':''}]
    for i in range(len(axis)):
        Out.putaxis(axis[i], i+1)
        Mask_Out.putaxis(axis[i], i+1)    
    Out.write(Array.data)
    Mask_Out.write(Array.mask)
    return

def MakeData(L, H, CorrTr, Cube, TraceH, S, Nh, Receivers):
    '''Makes a hypercube Shot, Time, Receiver and the associated header'''
    n=0
    for f in range(len(L)):
        if CorrTr[f] > 0:  ### correct for missing trace assume tailing
            Buff  = np.vstack((L[f], np.zeros((CorrTr[f],S ))))
            HBuff = np.vstack((H[f], np.zeros((CorrTr[f],Nh))))
        else:
            Buff  = L[f]
            HBuff = H[f]

        for i in range(0,len(Buff),Receivers):
            idx = n + i/Receivers
            Cube  [idx] =  Buff[i:i+Receivers].T
            TraceH[idx] = HBuff[i:i+Receivers].T
        n = idx +1
    return Cube, TraceH

#### File management    
Dir ='/path/to/your/Directory'
Files   =  ['Seis_A.rsf','Seis_B.rsf','Seis_C.rsf','Seis_D.rsf','Seis_E.rsf']
Headers = Files[:]
for a in range(len(Files)):
    Headers[a] = Files[a][:-4]+'T'+Files[a][-4:]

#### Data gathering
L, H, TT    = [], [], []
for m in range(len(Files)):
    DD, h = getData (Dir, Files[m], Headers[m])
    L.append(DD)
    H.append(h)
    TT.append(h[-1,1])

# This allows you to add traces in missing tape data without using the headers
#### Data consolidation
Receivers= H[0][0,-13]
Nh = len(H[0][0])
S = H[0][0,38]
CorrTr = [0,2,0,0,13] ##L[1] missing 2 traces L[4] missing 13 traces QC might be done directly from trace headers?
Tr = sum(TT+CorrTr)
Geom =(Tr/Receivers,S, Receivers) ## assuming first shot is correct
TraceH, Cube  = np.zeros((Geom[0], Nh, Receivers)), np.zeros(Geom)

### Then you can work on your data and make a cube offset/time/receivers
Cube, TraceH = MakeData(L, H, CorrTr, Cube, TraceH, S, Nh, Receivers)

### ... do some stuff with your data

#Export back to rsf
WriteRsf(Cube.transpose(0,2,1), Dir, 'Cube_test', Tsample=0.004, Rspacing=50) #Cube in Shot Time Offset needs ordering before export
WriteRsf(TraceH.transpose(0,2,1), Dir, 'Trace_test', Tsample=1, Rspacing=1)
