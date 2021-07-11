import myNotebook as nb
import sys
import json
import requests
from config import config
from theme import theme
import webbrowser
import os.path
from os import path

try:
    # Python 2
    import Tkinter as tk
    import ttk
except ModuleNotFoundError:
    # Python 3
    import tkinter as tk
    from tkinter import ttk

this = sys.modules[__name__]  # For holding module globals
this.VersionNo = "2.2.1"
this.FactionNames = []
this.TodayData = {}
this.YesterdayData = {}
this.DataIndex = 0
this.Status = "Active"
this.TickTime = ""
this.State = tk.IntVar()
this.MissionLog = []
this.MissionList = ['Mission_Courier_Elections_name', 'Mission_Delivery_name', 'Mission_AltruismCredits_name',
                    'Mission_Collect_Industrial_name', 'Mission_Delivery_Confederacy_name',
                    'Chain_HelpFinishTheOrder_name',
                    'MISSION_Salvage_Refinery_name', 'Mission_Rescue_Elections_name', 'Mission_Sightseeing_name',
                    'Mission_PassengerVIP_Tourist_ELECTION_name', 'Mission_PassengerBulk_AIDWORKER_ARRIVING_name',
                    'Mission_PassengerBulk_name']


def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    frame = nb.Frame(parent)
    nb.Label(frame, text="BGS Tally v" + this.VersionNo).grid(column=0, sticky=tk.W)
    nb.Checkbutton(frame, text="Make BGS Tally Active", variable=this.Status, onvalue="Active",
                   offvalue="Paused").grid()
    return frame


def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    this.StatusLabel["text"] = this.Status.get()


def plugin_start(plugin_dir):
    """
    Load this plugin into EDMC
    """
    this.Dir = plugin_dir
    file = os.path.join(this.Dir, "Today Data.txt")
    if path.exists(file):
        with open(file) as json_file:
            this.TodayData = json.load(json_file)
            z = len(this.TodayData)
            for i in range(1, z + 1):
                x = str(i)
                this.TodayData[i] = this.TodayData[x]
                del this.TodayData[x]
    file = os.path.join(this.Dir, "Yesterday Data.txt")
    if path.exists(file):
        with open(file) as json_file:
            this.YesterdayData = json.load(json_file)
            z = len(this.YesterdayData)
            for i in range(1, z + 1):
                x = str(i)
                this.YesterdayData[i] = this.YesterdayData[x]
                del this.YesterdayData[x]
    file = os.path.join(this.Dir, "MissionLog.txt")
    if path.exists(file):
        with open(file) as json_file:
            this.MissionLog = json.load(json_file)
    this.LastTick = tk.StringVar(value=config.get_str("XLastTick"))
    this.TickTime = tk.StringVar(value=config.get_str("XTickTime"))
    this.Status = tk.StringVar(value=config.get_str("XStatus"))
    this.DataIndex = tk.IntVar(value=config.get_int("xIndex"))
    this.StationFaction = tk.StringVar(value=config.get_str("XStation"))
    response = requests.get('https://api.github.com/repos/tezw21/BGS-Tally/releases/latest')  # check latest version
    latest = response.json()
    this.GitVersion = latest['tag_name']
    #  tick check and counter reset
    response = requests.get('https://elitebgs.app/api/ebgs/v5/ticks')  # get current tick and reset if changed
    tick = response.json()
    this.CurrentTick = tick[0]['_id']
    this.TickTime = tick[0]['time']
    if this.LastTick.get() != this.CurrentTick:
        this.LastTick.set(this.CurrentTick)
        this.YesterdayData = this.TodayData
        this.TodayData = {}
    return "BGS Tally v2"


def plugin_start3(plugin_dir):
    return plugin_start(plugin_dir)


def plugin_stop():
    """
    EDMC is closing
    """
    save_data()


def plugin_app(parent):
    """
    Create a frame for the EDMC main window
    """
    this.frame = tk.Frame(parent)
    Title = tk.Label(this.frame, text="BGS Tally v" + this.VersionNo)
    Title.grid(row=0, column=0, sticky=tk.W)
    if version_tuple(this.GitVersion) > version_tuple(this.VersionNo):
        title2 = tk.Label(this.frame, text="New version available", fg="blue", cursor="hand2")
        title2.grid(row=0, column=1, sticky=tk.W, )
        title2.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/tezw21/BGS-Tally/releases"))
    tk.Button(this.frame, text='Data Today', command=display_data).grid(row=1, column=0, padx=3)
    tk.Button(this.frame, text='Data Yesterday', command=display_yesterdaydata).grid(row=1, column=1, padx=3)
    tk.Label(this.frame, text="Status:").grid(row=2, column=0, sticky=tk.W)
    tk.Label(this.frame, text="Last Tick:").grid(row=3, column=0, sticky=tk.W)
    this.StatusLabel = tk.Label(this.frame, text=this.Status.get())
    this.StatusLabel.grid(row=2, column=1, sticky=tk.W)
    this.TimeLabel = tk.Label(this.frame, text=tick_format(this.TickTime)).grid(row=3, column=1, sticky=tk.W)
    return this.frame


def journal_entry(cmdr, is_beta, system, station, entry, state):
    EventList = ['Location', 'FSDJump', 'CarrierJump']
    if this.Status.get() != "Active":
        return
    if entry['event'] in EventList:  # get factions and populate today data
        this.FactionNames = []
        this.FactionStates = []
        z = 0
        try:
            test = entry['Factions']
        except KeyError:
            return
        for i in entry['Factions']:
            if i['Name'] != "Pilots' Federation Local Branch":
                this.FactionNames.append(i['Name'])
                this.FactionStates.append({'Faction': i['Name'], 'State': i['FactionState']})
                z += 1
        x = len(this.TodayData)
        if (x >= 1):
            for y in range(1, x + 1):
                if entry['StarSystem'] == this.TodayData[y][0]['System']:
                    this.DataIndex.set(y)
                    return
            this.TodayData[x + 1] = [
                {'System': entry['StarSystem'], 'SystemAddress': entry['SystemAddress'], 'Factions': []}]
            this.DataIndex.set(x + 1)
            z = len(this.FactionNames)
            for i in range(0, z):
                this.TodayData[x + 1][0]['Factions'].append(
                    {'Faction': this.FactionNames[i], 'FactionState': this.FactionStates[i]['State'],
                     'MissionPoints': 0,
                     'TradeProfit': 0, 'Bounties': 0, 'CartData': 0,
                     'CombatBonds': 0, 'MissionFailed': 0, 'Murdered': 0})
        else:
            this.TodayData = {
                1: [{'System': entry['StarSystem'], 'SystemAddress': entry['SystemAddress'], 'Factions': []}]}
            z = len(this.FactionNames)
            this.DataIndex.set(1)
            for i in range(0, z):
                this.TodayData[1][0]['Factions'].append(
                    {'Faction': this.FactionNames[i], 'FactionState': this.FactionStates[i]['State'],
                     'MissionPoints': 0,
                     'TradeProfit': 0, 'Bounties': 0, 'CartData': 0,
                     'CombatBonds': 0, 'MissionFailed': 0, 'Murdered': 0})
    
    if entry['event'] == 'Docked':  # enter system and faction named
        this.StationFaction.set(entry['StationFaction']['Name'])  # set controlling faction name
        #  tick check and counter reset
        response = requests.get('https://elitebgs.app/api/ebgs/v5/ticks')  # get current tick and reset if changed
        tick = response.json()
        this.CurrentTick = tick[0]['_id']
        this.TickTime = tick[0]['time']
        if this.LastTick.get() != this.CurrentTick:
            this.LastTick.set(this.CurrentTick)
            this.YesterdayData = this.TodayData
            this.TodayData = {}
            this.TimeLabel = tk.Label(this.frame, text=tick_format(this.TickTime)).grid(row=3, column=1, sticky=tk.W)
            theme.update(this.frame)
    
    if entry['event'] == 'MissionCompleted':  # get mission influence value
        fe = entry['FactionEffects']
        for i in fe:
            fe3 = i['Faction']
            if i['Influence'] != []:
                fe6 = i['Influence'][0]['SystemAddress']
                inf = len(i['Influence'][0]['Influence'])
                for y in this.TodayData:
                    if fe6 == this.TodayData[y][0]['SystemAddress']:
                        t = len(this.TodayData[y][0]['Factions'])
                        for z in range(0, t):
                            if fe3 == this.TodayData[y][0]['Factions'][z]['Faction']:
                                this.TodayData[y][0]['Factions'][z]['MissionPoints'] += inf
            else:
                for p in range(len(this.MissionLog)):
                    if this.MissionLog[p]["MissionID"] == entry["MissionID"]:
                        for y in this.TodayData:
                            if this.MissionLog[p]['System'] == this.TodayData[y][0]['System']:
                                for z in range(0, len(this.TodayData[y][0]['Factions'])):
                                    if this.TodayData[y][0]['Factions'][z]['Faction'] == fe3 and entry['Name'] in this.MissionList:
                                        this.TodayData[y][0]['Factions'][z]['MissionPoints'] += 1
        for count in range(len(this.MissionLog)):
            if this.MissionLog[count]["MissionID"] == entry["MissionID"]:
                this.MissionLog.pop(count)
                break
        save_data()
    
    if entry['event'] == 'SellExplorationData' or entry['event'] == "MultiSellExplorationData":  # get carto data value
        t = len(this.TodayData[this.DataIndex.get()][0]['Factions'])
        for z in range(0, t):
            if this.StationFaction.get() == this.TodayData[this.DataIndex.get()][0]['Factions'][z]['Faction']:
                this.TodayData[this.DataIndex.get()][0]['Factions'][z]['CartData'] += entry['TotalEarnings']
        save_data()
    
    if entry['event'] == 'RedeemVoucher' and entry['Type'] == 'bounty':  # bounties collected
        t = len(this.TodayData[this.DataIndex.get()][0]['Factions'])
        for z in entry['Factions']:
            for x in range(0, t):
                if z['Faction'] == this.TodayData[this.DataIndex.get()][0]['Factions'][x]['Faction']:
                    this.TodayData[this.DataIndex.get()][0]['Factions'][x]['Bounties'] += z['Amount']
        save_data()
    
    if entry['event'] == 'RedeemVoucher' and entry['Type'] == 'CombatBond':  # combat bonds collected
        print('Combat Bond redeemed')
        t = len(this.TodayData[this.DataIndex.get()][0]['Factions'])
        for x in range(0, t):
            if entry['Faction'] == this.TodayData[this.DataIndex.get()][0]['Factions'][x]['Faction']:
                this.TodayData[this.DataIndex.get()][0]['Factions'][x]['CombatBonds'] += entry['Amount']
        save_data()
    
    if entry['event'] == 'MarketSell':  # Trade Profit
        t = len(this.TodayData[this.DataIndex.get()][0]['Factions'])
        for z in range(0, t):
            if this.StationFaction.get() == this.TodayData[this.DataIndex.get()][0]['Factions'][z]['Faction']:
                cost = entry['Count'] * entry['AvgPricePaid']
                profit = entry['TotalSale'] - cost
                this.TodayData[this.DataIndex.get()][0]['Factions'][z]['TradeProfit'] += profit
        save_data()
    
    if entry['event'] == 'MissionAccepted':  # mission accpeted
        this.MissionLog.append({"Name": entry["Name"], "Faction": entry["Faction"], "MissionID": entry["MissionID"],
                                "System": system})
        save_data()
    
    if entry['event'] == 'MissionFailed':  # mission failed
        for x in range(len(this.MissionLog)):
            if this.MissionLog[x]["MissionID"] == entry["MissionID"]:
                for y in this.TodayData:
                    if this.MissionLog[x]['System'] == this.TodayData[y][0]['System']:
                        for z in range(0, len(this.TodayData[y][0]['Factions'])):
                            if this.MissionLog[x]['Faction'] == this.TodayData[y][0]['Factions'][z]['Faction']:
                                this.TodayData[y][0]['Factions'][z]['MissionFailed'] += 1
                this.MissionLog.pop(x)
                break
        save_data()
    
    if entry['event'] == 'MissionAbandoned':
        for x in range(len(this.MissionLog)):
            if this.MissionLog[x]["MissionID"] == entry["MissionID"]:
                this.MissionLog.pop(x)
        save_data()
    
    if entry['event'] == 'CommitCrime':
        if entry['CrimeType'] == 'murder':
            for y in this.TodayData:
                if system == this.TodayData[y][0]['System']:
                    for z in range(0, len(this.TodayData[y][0]['Factions'])):
                        if entry['Faction'] == this.TodayData[y][0]['Factions'][z]['Faction']:
                            this.TodayData[y][0]['Factions'][z]['Murdered'] += 1


def version_tuple(version):
    try:
        ret = tuple(map(int, version.split(".")))
    except:
        ret = (0,)
    return ret


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def display_data():
    form = tk.Toplevel(this.frame)
    form.title("BGS Tally v" + this.VersionNo + " - Data Today")
    form.geometry("800x280")
    tab_parent = ttk.Notebook(form)
    for i in this.TodayData:
        tab = ttk.Frame(tab_parent)
        tab_parent.add(tab, text=this.TodayData[i][0]['System'])
        FactionLabel = tk.Label(tab, text="Faction")
        FactionStateLabel = tk.Label(tab, text="Faction State")
        MPLabel = tk.Label(tab, text="Misson Points")
        TPLabel = tk.Label(tab, text="Trade Profit")
        BountyLabel = tk.Label(tab, text="Bounties")
        CDLabel = tk.Label(tab, text="Cart Data")
        CombatLabel = tk.Label(tab, text="Combat Bonds")
        FailedLabel = tk.Label(tab, text="Mission Failed")
        MurderLabel = tk.Label(tab, text="Murdered")
        FactionLabel.grid(row=0, column=0)
        FactionStateLabel.grid(row=0, column=1)
        MPLabel.grid(row=0, column=2)
        TPLabel.grid(row=0, column=3)
        BountyLabel.grid(row=0, column=4)
        CDLabel.grid(row=0, column=5)
        CombatLabel.grid(row=0, column=6)
        FailedLabel.grid(row=0, column=7)
        MurderLabel.grid(row=0, column=8)
        z = len(this.TodayData[i][0]['Factions'])
        for x in range(0, z):
            FactionName = tk.Label(tab, text=this.TodayData[i][0]['Factions'][x]['Faction'])
            FactionName.grid(row=x + 1, column=0, sticky=tk.W)
            FactionState = tk.Label(tab, text=this.TodayData[i][0]['Factions'][x]['FactionState'])
            FactionState.grid(row=x + 1, column=1)
            Missions = tk.Label(tab, text=this.TodayData[i][0]['Factions'][x]['MissionPoints'])
            Missions.grid(row=x + 1, column=2)
            Trade = tk.Label(tab, text=human_format(this.TodayData[i][0]['Factions'][x]['TradeProfit']))
            Trade.grid(row=x + 1, column=3)
            Bounty = tk.Label(tab, text=human_format(this.TodayData[i][0]['Factions'][x]['Bounties']))
            Bounty.grid(row=x + 1, column=4)
            CartData = tk.Label(tab, text=human_format(this.TodayData[i][0]['Factions'][x]['CartData']))
            CartData.grid(row=x + 1, column=5)
            Failed = tk.Label(tab, text=this.TodayData[i][0]['Factions'][x]['MissionFailed'])
            Failed.grid(row=x + 1, column=7)
            Combat = tk.Label(tab, text=human_format(this.TodayData[i][0]['Factions'][x]['CombatBonds']))
            Combat.grid(row=x + 1, column=6)
            Murder = tk.Label(tab, text=this.TodayData[i][0]['Factions'][x]['Murdered'])
            Murder.grid(row=x + 1, column=8)
    tab_parent.pack(expand=1, fill='both')


def display_yesterdaydata():
    form = tk.Toplevel(this.frame)
    form.title("BGS Tally v" + this.VersionNo + " - Data Yesterday")
    form.geometry("800x280")
    tab_parent = ttk.Notebook(form)
    for i in this.YesterdayData:
        tab = ttk.Frame(tab_parent)
        tab_parent.add(tab, text=this.YesterdayData[i][0]['System'])
        FactionLabel = tk.Label(tab, text="Faction")
        FactionStateLabel = tk.Label(tab, text="Faction State")
        MPLabel = tk.Label(tab, text="Misson Points")
        TPLabel = tk.Label(tab, text="Trade Profit")
        BountyLabel = tk.Label(tab, text="Bounties")
        CDLabel = tk.Label(tab, text="Cart Data")
        CombatLabel = tk.Label(tab, text="Combat Bonds")
        FailedLabel = tk.Label(tab, text="Mission Failed")
        MurderLabel = tk.Label(tab, text="Murdered")
        FactionLabel.grid(row=0, column=0)
        FactionStateLabel.grid(row=0, column=1)
        MPLabel.grid(row=0, column=2)
        TPLabel.grid(row=0, column=3)
        BountyLabel.grid(row=0, column=4)
        CDLabel.grid(row=0, column=5)
        CombatLabel.grid(row=0, column=6)
        FailedLabel.grid(row=0, column=7)
        MurderLabel.grid(row=0, column=8)
        z = len(this.YesterdayData[i][0]['Factions'])
        for x in range(0, z):
            FactionName = tk.Label(tab, text=this.YesterdayData[i][0]['Factions'][x]['Faction'])
            FactionName.grid(row=x + 1, column=0, sticky=tk.W)
            FactionState = tk.Label(tab, text=this.YesterdayData[i][0]['Factions'][x]['FactionState'])
            FactionState.grid(row=x + 1, column=1)
            Missions = tk.Label(tab, text=this.YesterdayData[i][0]['Factions'][x]['MissionPoints'])
            Missions.grid(row=x + 1, column=2)
            Trade = tk.Label(tab, text=human_format(this.YesterdayData[i][0]['Factions'][x]['TradeProfit']))
            Trade.grid(row=x + 1, column=3)
            Bounty = tk.Label(tab, text=human_format(this.YesterdayData[i][0]['Factions'][x]['Bounties']))
            Bounty.grid(row=x + 1, column=4)
            CartData = tk.Label(tab, text=human_format(this.YesterdayData[i][0]['Factions'][x]['CartData']))
            CartData.grid(row=x + 1, column=5)
            Combat = tk.Label(tab, text=human_format(this.YesterdayData[i][0]['Factions'][x]['CombatBonds']))
            Combat.grid(row=x + 1, column=6)
            Failed = tk.Label(tab, text=this.YesterdayData[i][0]['Factions'][x]['MissionFailed'])
            Failed.grid(row=x + 1, column=7)
            Murder = tk.Label(tab, text=this.YesterdayData[i][0]['Factions'][x]['Murdered'])
            Murder.grid(row=x + 1, column=8)
    tab_parent.pack(expand=1, fill='both')


def tick_format(ticktime):
    datetime1 = ticktime.split('T')
    x = datetime1[0]
    z = datetime1[1]
    y = x.split('-')
    if y[1] == "01":
        month = "Jan"
    elif y[1] == "02":
        month = "Feb"
    elif y[1] == "03":
        month = "March"
    elif y[1] == "04":
        month = "April"
    elif y[1] == "05":
        month = "May"
    elif y[1] == "06":
        month = "June"
    elif y[1] == "07":
        month = "July"
    elif y[1] == "08":
        month = "Aug"
    elif y[1] == "09":
        month = "Sep"
    elif y[1] == "10":
        month = "oct"
    elif y[1] == "11":
        month = "nov"
    elif y[1] == "12":
        month = "Dec"
    date1 = y[2] + " " + month
    time1 = z[0:5]
    datetimetick = time1 + ' UTC ' + date1
    return (datetimetick)


def save_data():
    config.set('XLastTick', this.CurrentTick)
    config.set('XTickTime', this.TickTime)
    config.set('XStatus', this.Status.get())
    config.set('XIndex', this.DataIndex.get())
    config.set('XStation', this.StationFaction.get())
    file = os.path.join(this.Dir, "Today Data.txt")
    with open(file, 'w') as outfile:
        json.dump(this.TodayData, outfile)
    file = os.path.join(this.Dir, "Yesterday Data.txt")
    with open(file, 'w') as outfile:
        json.dump(this.YesterdayData, outfile)
    file = os.path.join(this.Dir, "MissionLog.txt")
    with open(file, 'w') as outfile:
        json.dump(this.MissionLog, outfile)
