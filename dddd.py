import fnmatch
import tempfile
import os
from zipfile import ZipFile, ZIP_DEFLATED

ZIP_PATH = "C:\\Users\\David Zalewski\\Saved Games\\DCS\\Missions\\dcs_dnd_campaign\\dcs_dnd_campaign_turn_01R - Copy.miz"
NEW_ZIP_PATH = "C:\\Users\\David Zalewski\\Saved Games\\DCS\\Missions\\dcs_dnd_campaign\\dcs_dnd_campaign_turn_01R - NEW NEW NEW.miz"

zfile = ZipFile(ZIP_PATH, 'r')
files = []
for name in zfile.namelist():
    if fnmatch.fnmatch(name, '*mission'):
        files.append(zfile.read(name))

print("hello")

def updateZip(zipname, newzipname, filename, data):
    # generate a temp file
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
    os.close(tmpfd)

    # create a temp copy of the archive without filename
    with ZipFile(zipname, 'r') as zin:
        with ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    with ZipFile(tmpname, mode='a', compression=ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)

    # replace with the temp archive
    os.rename(tmpname, newzipname)


updateZip(ZIP_PATH, NEW_ZIP_PATH, 'mission', "mission = {}")