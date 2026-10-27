# WLWBX Assistant

⚠️ **Still in progress!** ⚠️

**This project is neither developed nor supported by the wallbox manufacturer.**

The project is based on on the official API documetation of the Steca Charger:
[WLWBX REST API](https://public.evse-manuals.com/steca/de/specs/api.html#description/introduction)

WLWBX Assistent is an unofficial Home Assistant integration.

The code is made with support of AI!

## Features

| Feature | Steca Charger| 
|------------|:--------------:|
| Charging state |🟢|
| Direct charging authorization ​|🟢|
| Free charging mode |🟢|
| Set user limit of charging current |🟢|
| Get charging curve data​ |🟡|
| Get lifetime statistics​ |🟡|
| Get info about software updates of the Wallbox |🟡|
| Get system errors |🔵|
| Delete all errors |🔵|
| Get electronic typeplate |🟢|
| Get device temperatures |🔵|
| Server-sent event stream publishing events and value updates |🟡|
| Login |🟢|
| Refresh access token |🟢|
| performs the reboot action |🔵|


🟢 Implemented an tested
🟡 Implemented, has to be tested
🔴 not working
🔵 planed

## Installation
1. clone this repository
2. copy the files in `/custom_components/wlwbx` in our Home Assistant
3. reboot Home Assistant
   
## Configuration
1. go to Settings
2. open "Devices & Services"
3. click on "Add integration" on the right side
4. search for "WLWBX Assistant"
5. write the the necessary informations into the fields
  - Host: the IP-adress or hostname of the box
  - Username: technician (don´t change that)
  - Password: Your technician password
  - verify_ssl: check this only if you use a reverse proxy with ssl

## Disclaimer

This project is an independent, community-developed Home Assistant integration.

It is not affiliated with, endorsed by, or sponsored by any related company.

All trademarks, product names and company names are the property of their respective owners.

This software is provided "as is" without warranty of any kind. Use at your own risk.
The authors assume no responsibility for damage, data loss, charging interruptions, configuration issues, or other consequences resulting from the use of this software.



