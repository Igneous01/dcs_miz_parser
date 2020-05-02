from slpp import slpp as lua
from pathlib import Path

MISSION_PATH = "C:\\Users\\David Zalewski\\Saved Games\\DCS\\Missions\\dcs_dnd_campaign\\extracted_mission\\mission"
DICT_PATH = "C:\\Users\\David Zalewski\\Saved Games\\DCS\\Missions\\dcs_dnd_campaign\\extracted_mission\\l10n\\DEFAULT\\dictionary"
RESULTS_PATH = "C:\\Users\\David Zalewski\\Saved Games\\DCS\\Missions\\dcs_dnd_campaign\\t01r_s1.log"

miz_contents = Path(MISSION_PATH).read_text(encoding='utf-8')[10:]
dict_contents = Path(DICT_PATH).read_text(encoding='utf-8')[13:]
results_contents = Path(RESULTS_PATH).read_text(encoding='utf-8')[13:]

miz = lua.decode(miz_contents)
results = lua.decode(results_contents)
miz_dict = lua.decode(dict_contents)

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


class DeleteKeyPath:
    coalition = ''
    country = ''
    dcs_type = ''
    group = ''
    unit = ''
    group_name = ''
    unit_type = ''
    new_index = ''

    def __init__(self, coalition, country, dcs_type, group, unit, group_name, unit_type):
        self.coalition = coalition
        self.country = country
        self.dcs_type = dcs_type
        self.group = group
        self.unit = unit
        self.group_name = group_name,
        self.unit_type = unit_type


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
    del grp["units"][utd.unit]

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


with open("Output.txt", "w", encoding='utf-8') as text_file:
    print("mission = " + lua.encode(miz), file=text_file)














#coalition.blue.country[0].static.group[0].units[0].name
#coalition.blue.country[0].aircraft.group[0].units[0].name
#coalition.blue.country[0].vehicle.group[0].units[0].name
#coalition.blue.country[0].helicopter.group[0].units[0].name
#coalition.red.country[0].static.group[0].units[0].name
#coalition.red.country[0].aircraft.group[0].units[0].name
#coalition.red.country[0].vehicle.group[0].units[0].name
#coalition.red.country[0].helicopter.group[0].units[0].name



























#m = dcs.Mission()

#successLoad = m.load_file('C:\\Users\\David Zalewski\\Saved Games\\DCS\\Missions\\dcs_dnd_campaign\\dcs_dnd_campaign_turn_01R_After_Sortie_1.miz')

#g = m.find_group('T-55 Company', 'match')

#print(g.name)