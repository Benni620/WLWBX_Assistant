# Changelog

## [v0.2.1]

### Fixed

- Fixed NameError (import WlwbxApiError from .api)
- Fixed 403 error is treated as an incorrect password
- Fixed missing translations
- Fixed 401 was ignored after logging in again
- Fixed A 403 error on a REQUIRED endpoint was ignored
- Fixed No unique ID protection

## [v0.2.1-alpha.1]

### Fixed

- Fixed NameError (import WlwbxApiError from .api)
- Fixed 403 error is treated as an incorrect password
- Fixed missing translations
- Fixed 401 was ignored after logging in again
- A 403 error on a REQUIRED endpoint was ignored
- No unique ID protection

## [v0.2.0]

### Added

**Monitoring & Statistics**
- Errors with a complete description and corrective actions in text.

**Charging Control**
- Charging state with binary switches

**Device Information & Maintenance**
- perform reboot
- get and set the state of the socket outlet
- Added: Ability to change password and IP/hostname

### Fixed

- Fixed Config-Flow, It won't be added if you enter the wrong password.
- Fixed Auth-Failure + Reauth-Flow, automatically starts the re-authentication process and doesn't get stuck in a never-ending retry loop
- Fixed socket lock on cable version

### Removed

- Removed Firmware-Install (Cannot be tested yet without the new software; therefore, the feature has been disabled as a precaution)
- Removed Reboot action (This is currently not possible due to the software's user permissions on the device.)

## [v0.2.0-alpha.3.2] 

### Added

- Added: Ability to change password and IP/hostname 

## [v0.2.0-alpha.3] 

### Fixed

- Fixed Config-Flow, It won't be added if you enter the wrong password.
- Fixed Auth-Failure + Reauth-Flow, automatically starts the re-authentication process and doesn't get stuck in a never-ending retry loop

### Removed

- Removed Firmware-Install
- Removed Reboot action

## [v0.2.0-alpha.2.1] 

### Fixed

- Fixed missing file
- Fixed socket lock on cable version
- Fixed get reboot enabled state for the reboot action

## [v0.2.0-alpha.2] 

### Added

**Charging Control**
- Charging state with binary switches

**Device Information & Maintenance**
- perform reboot
- get and set the state of the socket outlet

## [v0.2.0-alpha.1] 

### Added

**Monitoring & Statistics**
- Errors with a complete description and corrective actions in text.

## [v0.1.2]

### Fixed
- Fixed coordinator data access across sensor, switch, number, button and update platforms.
- Fixed integration setup in Home Assistant.
  
## [v0.1.1]

### Fixed
- Fixed integration domain mismatch preventing the configuration flow from loading.
- Fixed integration setup in Home Assistant.

## [v0.1.0] - Initial Release

### Added

**Connection & Authentication**
- Login via JWT authentication
- Automatic access token refresh

**Charging Control**
- Charging state monitoring
- Direct charging authorization
- Get and set free charging mode
- Get and set user charging current limit

**Monitoring & Statistics**
- Charging curve data
- Lifetime charging statistics
- Device temperatures
- Energy meter information

**Device Information & Maintenance**
- Electronic type plate information
- Retrieve and delete device errors
