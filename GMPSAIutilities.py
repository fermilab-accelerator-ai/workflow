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
        finallist.append(cleanline)
    if debug: print (finallist)
    return finallist


if __name__ == "__main__":
    getParamListFromTextFile(debug=True)

