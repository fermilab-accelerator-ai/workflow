import os.path

def getParamListFromTextFile(textfilename='ParamList.txt', debug=False):
    if debug: print ('getParamListFromTextFile: Opening '+textfilename)
    # Bail if no file by that name
    if not os.path.isfile(textfilename): exit ('File '+textfilename+' is not a file.')
    textfile = open(textfilename,'r')
    lines = textfile.readlines()
    finallist = []
    for line in lines:
        cleanline = line.strip()
        # This is where we could check for valid param name format. Could. 
        parts = cleanline.split()
        if not len(parts) == 2: 
            print (line+"  ...unable to parse node and device.")
            continue
        node,device = parts[0],parts[1]
        finallist.append([node,device])
    if debug: print (finallist)
    return finallist


if __name__ == "__main__":
    getParamListFromTextFile(debug=True)

