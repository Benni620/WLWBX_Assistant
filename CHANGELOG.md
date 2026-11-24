# Changelog

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

## [0.1.2]

### Fixed
- Fixed coordinator data access across sensor, switch, number, button and update platforms.
- Fixed integration setup in Home Assistant.
  
## [0.1.1]

### Fixed
- Fixed integration domain mismatch preventing the configuration flow from loading.
- Fixed integration setup in Home Assistant.

## [0.1.0] - Initial Release

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
