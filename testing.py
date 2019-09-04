import argparse
import math
import h5py
import pandas as pd
import matplotlib.pyplot as plt
from progress.bar import Bar
import seaborn as sns

debug=True
dfmaxrow= 120

#infilename = '/pnfs/ldrd/accelai/tape/MLParamData_1562734866.2472222_From_MLrn_2019-07-09+00:00:00_to_2019-07-10+00:00:00.h5'


try: 
    df = pd.read_hdf('test.h5')
except Exception as e:
    infilename = '/pnfs/ldrd/accelai/tape/MLParamData_1560458101.9999847_From_MLrn_2019-06-03+00:00:00_to_2019-06-04+00:00:00.h5'
    df = pd.read_hdf(infilename, 'B:VIMIN')
    df['B_VIMIN']  = pd.read_hdf(infilename, 'B_VIMIN')['B_VIMIN']
    df['B:IMINER'] = pd.read_hdf(infilename, 'B:IMINER')['B:IMINER']

    alpha = 8.5e-2
    beta_nought = 1e-3
    gamma = 0.75350088e-5

    # Iteratively construct the series Beta
    # Start from all zeroes
    df['beta'] = df.apply(lambda x: beta_nought, axis=1)
    # Formula is iterative; cannot parallellize?
    bar = Bar('Calculating', max=len(df))
    for i in range(1 ,len(df)): # skip zeroth entry
        if math.isnan(df.at[i-1,'beta']) or math.isnan(df.at[i,'B:IMINER']): continue
        df.at[i,'beta'] = df.at[i-1,'beta'] + gamma*df.at[i,'B:IMINER']
        bar.next()
    bar.finish()
    # Here's the big calculation
    df['calcVIMIN'] = df['B_VIMIN'] - alpha*df['B:IMINER'] - df['beta']
    # Fine. Save it out.
    df.to_hdf('test.h5',mode='w', key='testdf')
    print (df)


df = df.truncate(after=dfmaxrow)
df['fittedmin'] = df['B_VIMIN'] + df['B:IMINER']/10.0
df['datetime'] = pd.to_datetime(df['utc_secondsB:VIMIN'],unit='s', yearfirst=True)


plt.figure(figsize=(8, 6))
sns.set(style="darkgrid")
plt.subplot(211)
serieslist = ['B_VIMIN','fittedmin','B:VIMIN','calcVIMIN']
sns.lineplot(x='datetime', y='B_VIMIN'  , data=df)
sns.lineplot(x='datetime', y='fittedmin', data=df)
sns.lineplot(x='datetime', y='B:VIMIN'  , data=df)
sns.lineplot(x='datetime', y='calcVIMIN', data=df)
plt.legend(labels = serieslist, loc='upper right')
plt.savefig('testplot.png')

plt.figure(figsize=(8, 6))
plt.subplot(211)
df['meander'] = df['fittedmin'] - df['B_VIMIN']
df['Rx']      = df['B:VIMIN']   - df['B_VIMIN']
df['calcRx']  = df['calcVIMIN'] - df['B_VIMIN']
sns.lineplot(x='datetime', y='meander', data=df)
sns.lineplot(x='datetime', y='Rx'     , data=df)
sns.lineplot(x='datetime', y='calcRx' , data=df)
plt.legend(labels=['meander', 'Rx', 'calcRx'], loc='upper right')
plt.ylabel('Amperes') 
plt.xlabel('') 
plt.gca().xaxis.set_ticklabels([]) # Same as plot below
plt.subplot(212)
df['appliedRx'] = df['meander']+df['Rx']
df['appliedcalcRx'] = df['meander']+df['calcRx']
sns.lineplot(x='datetime', y='appliedRx', data=df)
sns.lineplot(x='datetime', y='appliedcalcRx', data=df)
plt.legend(labels=['appliedRx','appliedcalcRx'], loc='upper right')
plt.ylabel('Amperes') 
plt.savefig('testplot2.png')
