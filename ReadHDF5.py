import h5py
import pandas as pd
import numpy as np

infilename = 'MLData_1561566500.076893_From_EventC_2019-06-25+23:59:59_to_2019-06-26+00:00:00.h5'
hf = h5py.File(infilename, 'r')


# List all groups
print("Keys: %s" % hf.keys())
a_group_key = list(hf.keys())[0]

# Get the data, just print it to stdout
for k in hf.keys():
    dsgroup = hf.get(k)
    df = pd.read_hdf(infilename, k)
    print (k,':\n', df)


    
