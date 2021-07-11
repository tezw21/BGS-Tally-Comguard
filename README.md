# BGS-Tally V2.2.0
An EDMC plugin to count BGS work

Now compatible with Python 3 release


# Installation
Download the [latest release](https://github.com/tezw21/BGS-Tally-v2.0/releases/tag/2.2.2) of BGS Tally
 - In EDMC, on the Plugins settings tab press the “Open” button. This reveals the plugins folder where this app looks for plugins.
 - Open the .zip archive that you downloaded and move the folder contained inside into the plugins folder.

You will need to re-start EDMC for it to notice the new plugin.

# Usage
BGS Tally v2.0 counts all the BGS work you do for any faction, in any system. 
It is highly recommended that EDMC is started before ED is launched as Data is recorded at startup and then when you dock at a station. Not doing this can result in missing data.
The data is shown on a pop up window when the Data Today button on the EDMC main screen is pushed.
The plugin can paused in the BSG Tally v2.0 tab in settings.

From v2.2 we count the following activities. 
- Mission inf +
- Total trade profit sold to Faction controlled station
- Cartographic data sold to Faction controlled station
- Bounties issued by named Faction.
- Combat Bonds issued by named Faction
- Missions Failed for named Faction
- Ships murdered owned by named Faction
- Missions are counted when a Faction is in Election. Only missions that my research suggests work during Election are counted, this is a work in progress
- Negative trade is counted with a minus sign in trade profit column.

These total during the session and reset at server tick.
The state column has 3 options, None, War or Election to give an indication on how missions are being counted
