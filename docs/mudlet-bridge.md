# Mudlet Bridge

`python -m dd4tester mudlet-bridge --directory <shared-directory>` creates a
small shared-file adapter for a visible Mudlet profile. Put the directory in a
Windows location that the virtual machine can access, such as a VirtualBox
shared folder. It creates:

- `dd4tester_bridge.lua`: import this into the DD4 Mudlet profile as a script.
- `commands.txt`: DD4Tester appends one safe game command per line.
- `events.jsonl`: Mudlet records dispatched commands and GMCP snapshots here.

The generated script polls the command inbox, sends commands with
`send(command, true)`, captures the GMCP packages consumed by the existing
DD4Tester observation/state reducer, and installs its own line trigger for the
ordinary MUD text transcript. Re-importing the script replaces its line
trigger, GMCP handlers, and polling timer so an updated bridge does not emit
duplicate events. Its JSON encoder preserves GMCP arrays such as affects,
inventory, and equipment. It deliberately does not handle login credentials;
keep those in Windows Credential Manager and the Mudlet profile.

The Python bridge reduces `events.jsonl` through `ObservationParser`, the same
parser used by the direct Telnet runner. A HERO request can select this path:

```powershell
python -m dd4tester hero --race human --sex female --class mage --transport mudlet --mudlet-directory <shared-directory>
```

The direct policy runner then reads the Mudlet events and writes decisions to
the command inbox using the same persistent campaign, transcript, and SQLite
records as Telnet. Selecting Mudlet through `hero` also generates these files
automatically. At startup it consumes the current bridge snapshot so a profile
already connected to DD4 can establish its prompt and GMCP state. This still
does not launch a VM or configure a Mudlet profile; those visible-client
lifecycle steps remain to be automated.
