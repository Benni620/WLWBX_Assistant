# WLWBX Assistant

⚠️ **Still in progress** ⚠️

The project is based on on the official API documetation of the Steca Charger:
[WLWBX REST API](https://public.evse-manuals.com/steca/de/specs/api.html#description/introduction)

This is an integration of the Steca Charger for Home Assistant

The code is made with support of AI!

## Fatures

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


🟢 Implemeted an tested
🟡 Implemented, has to be tested
🔴 not working
🔵 planed

## Installation
1. clone this repository
2. copy the files in `/custom_components/wlwbx` in our Home Assistant
3. reboot Home Assistant
   
## Configuration
1. go to Settings
2. open Devices & services
3. klick on Add integration on the right side
4. search for "WLWBX Assistant"
5. write the the necessary information into the filds
  - Host: the IP-adress or Hostname of the box
  - Username: technician (don´t change that)
  - Password: Your technician password
  - verify_ssl: check this only if you use a reverse proxy with ssl
