from slpp import slpp as lua
from pathlib import Path
import fnmatch
import tempfile
import os
from zipfile import ZipFile, ZIP_DEFLATED
from sys import argv


class DeleteKeyPath:
    coalition = ''
    country = ''
    dcs_type = ''
    group = ''
    unit_index = ''
    group_name = ''
    unit_type = ''
    new_index = ''

    def __init__(self, coalition, country, dcs_type, group, unit_index, group_name, unit_type):
        self.coalition = coalition
        self.country = country
        self.dcs_type = dcs_type
        self.group = group
        self.unit_index = unit_index
        self.group_name = group_name,
        self.unit_type = unit_type


script, miz_path, dcs_log_path, new_miz_path = argv

print("miz path:", miz_path)
print("dcs log path:", dcs_log_path)
print("new miz path:", new_miz_path)

miz_file = ZipFile(miz_path, 'r')
mission_file_bytes = ''
dictionary_file_bytes = ''

for name in miz_file.namelist():
    if fnmatch.fnmatch(name, '*mission'):
        print("reading ", name)
        mission_file_bytes = miz_file.read(name)[10:]
    if fnmatch.fnmatch(name, '*dictionary'):
        print("reading ", name)
        dictionary_file_bytes = miz_file.read(name)[13:]

print("reading ", dcs_log_path)
dcs_log_contents = Path(dcs_log_path).read_text(encoding='utf-8')[13:]

miz = lua.decode(mission_file_bytes.decode("utf-8"))
miz_dict = lua.decode(dictionary_file_bytes.decode("utf-8"))
results = lua.decode(dcs_log_contents)

dead_events = []
events = results.get("events")
for key, v in events.items():
    if v["type"] == 'dead' or v["type"] == "eject" or v["type"] == "pilot dead":
        dead_events.append(v)

for e in dead_events:
    try:
        keyFromVal = list(miz_dict.values()).index(e["initiator"])
        e["dictKey"] = list(miz_dict.keys())[keyFromVal]
    except ValueError:
        e["dictKey"] = keyFromVal

units_to_delete = []


def process_miz(coalition, dcs_type):
    countries = miz["coalition"][coalition]["country"]
    for countryIndex, country in countries.items():
        if dcs_type in country and "group" in country[dcs_type]:
            for groupIndex, group in country[dcs_type]["group"].items():
                if "units" in group:
                    for unitIndex, unit in group["units"].items():
                        for deadUnit in dead_events:
                            if unit["name"] == deadUnit["dictKey"]:
                                units_to_delete.append(DeleteKeyPath(coalition, countryIndex, dcs_type, groupIndex, unitIndex, group["name"], unit["type"]))


print("processing miz file")
process_miz("red", "static")
process_miz("red", "plane")
process_miz("red", "vehicle")
process_miz("red", "helicopter")
process_miz("blue", "static")
process_miz("blue", "plane")
process_miz("blue", "vehicle")
process_miz("blue", "helicopter")

units_to_reindex = []
groups_to_reindex = []
groups_to_delete = []

# delete all units first
for utd in units_to_delete:
    grp = miz["coalition"][utd.coalition]["country"][utd.country][utd.dcs_type]["group"][utd.group]
    del grp["units"][utd.unit_index]

    if len(grp["units"]) == 0:
        groups_to_delete.append(utd)
        groups_to_reindex.append(miz["coalition"][utd.coalition]["country"][utd.country][utd.dcs_type])
    else:
        units_to_reindex.append(grp)

# reindex all units
for grp in units_to_reindex:
    new_unit_index = 1
    translate = {}
    units_dict = grp["units"]
    for unit_index, unit in units_dict.items():
        utd.new_index = new_unit_index
        translate[unit_index] = new_unit_index
        new_unit_index += 1
    for old_key, new_key in translate.items():
        units_dict[new_key] = units_dict.pop(old_key)

# delete all groups with empty units
for utd in groups_to_delete:
    del miz["coalition"][utd.coalition]["country"][utd.country][utd.dcs_type]["group"][utd.group]

# reindex all group indexes
for cntry in groups_to_reindex:
    new_unit_index = 1
    translate = {}
    group_dict = cntry["group"]
    for unit_index, unit in group_dict.items():
        utd.new_index = new_unit_index
        translate[unit_index] = new_unit_index
        new_unit_index += 1
    for old_key, new_key in translate.items():
        group_dict[new_key] = group_dict.pop(old_key)


def update_zip(zip_name, new_zip_name, filename, data):
    # generate a temp file
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zip_name))
    os.close(tmpfd)

    # create a temp copy of the archive without filename
    with ZipFile(zip_name, 'r') as zin:
        with ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    with ZipFile(tmpname, mode='a', compression=ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)

    # replace with the temp archive
    os.rename(tmpname, new_zip_name)


print("creating new miz file")
new_miz_data = "mission = " + lua.encode(miz)
update_zip(miz_path, new_miz_path, "mission", new_miz_data)
