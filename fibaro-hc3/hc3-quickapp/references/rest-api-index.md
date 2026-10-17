# HC3 REST API — full endpoint index (firmware 5.2xx swagger)

Generated with `scripts/swagger_index.py` from the official swagger of a 5.220 box. Paths are given with the
`/api` prefix used from a computer; inside a QuickApp call `api.get("/devices")` without it. Search this file with
grep rather than reading it whole. Undocumented-but-used endpoints are in `rest-api.md`.

### additionalinterfaces

| Method and path | Summary |
|---|---|
| `GET /api/additionalInterfaces` | Get list of all additional interfaces |
| `GET /api/additionalInterfaces/{interfaceName}` | Get list of all devices id which can add this additional interface. |

### alarms-devices

| Method and path | Summary |
|---|---|
| `GET /api/alarms/v1/devices/` | Get alarm devices |

### alarms-history

| Method and path | Summary |
|---|---|
| `GET /api/alarms/v1/history/` | Get alarm history entries |

### alarms-partitions

| Method and path | Summary |
|---|---|
| `GET /api/alarms/v1/partitions` | Get all alarm partitions |
| `POST /api/alarms/v1/partitions` | Creates new alarm partition. The partition will be disarmed by default. |
| `GET /api/alarms/v1/partitions/breached` | Get breached partition ids |
| `GET /api/alarms/v1/partitions/{partitionID}` | Get existing partition |
| `PUT /api/alarms/v1/partitions/{partitionID}` | Update existing partition |
| `DELETE /api/alarms/v1/partitions/{partitionID}` | Delete existing partition |
| `POST /api/alarms/v1/partitions/actions/tryArm` | Try to arm all alarm partitions after sensor breached status verification |
| `POST /api/alarms/v1/partitions/actions/arm` | Arm all alarm partitions |
| `DELETE /api/alarms/v1/partitions/actions/arm` | Disarm all alarm partitions |
| `POST /api/alarms/v1/partitions/{partitionID}/actions/tryArm` | Try to arm alarm partition after sensor breached status verification |
| `POST /api/alarms/v1/partitions/{partitionID}/actions/arm` | Arm alarm partition |
| `DELETE /api/alarms/v1/partitions/{partitionID}/actions/arm` | Disarm alarm partition |

### analytics

| Method and path | Summary |
|---|---|
| `POST /api/analytics` | Retrieves analytics data |

### categories

| Method and path | Summary |
|---|---|
| `GET /api/categories` | List of supported categories |

### consumption

| Method and path | Summary |
|---|---|
| `GET /api/energy/{timestampFrom}/{timestampTo}/{dataSet}/{type}/{unit}/{id}` | Get energy from/to |
| `GET /api/panels/energy?id={id}` | Get energy |
| `GET /api/coPlot?id={id}&from={timestampFrom}&to={timestampTo}` | Get co from/to |
| `GET /api/temperature/{timestampFrom}/{timestampTo}/{dataSet}/{type}/temperature/{id}` | Get temperature from/to |
| `GET /api/smokeTemperature/{timestampFrom}/{timestampTo}/{dataSet}/{type}/smoke/{id}` | Get smoke from/to |
| `GET /api/thermostatTemperature/{timestampFrom}/{timestampTo}/{dataSet}/{type}/thermostat/{id}` | Get thermostat from/to |

### debugmessages

| Method and path | Summary |
|---|---|
| `GET /api/debugMessages` | Get a list of debug messages |
| `DELETE /api/debugMessages` | Delete debug messages |
| `GET /api/debugMessages/tags` | Get a list of defined debug tags |

### devicenotifications

| Method and path | Summary |
|---|---|
| `GET /api/deviceNotifications/v1` | Get information about device notifications settings |
| `GET /api/deviceNotifications/v1/{deviceID}` | Get notifications settings for given device |
| `PUT /api/deviceNotifications/v1/{deviceID}` | Update notifications settings for given device |
| `DELETE /api/deviceNotifications/v1/{deviceID}` | Clear notifications settings for given device |

### devices

| Method and path | Summary |
|---|---|
| `GET /api/devices` | Get list of available devices for authenticated user |
| `POST /api/devices` | Create plugin |
| `POST /api/devices/filter` | Get list of filtered devices available for authenticated user |
| `POST /api/devices/addInterface` | Add interfaces to devices |
| `POST /api/devices/deleteInterface` | Delete interfaces from devices |
| `GET /api/devices?property=[lastLoggedUser,{userId}]` | Get mobile device list for user with specified id |
| `POST /api/devices/groupAction/{actionName}` | Call group action |
| `GET /api/devices/{deviceID}` | Get device object |
| `PUT /api/devices/{deviceID}` | Modify device |
| `DELETE /api/devices/{deviceID}` | Delete device |
| `DELETE /api/slave/{uuid}/api/devices/{deviceID}` | Delete device using master as a proxy for slave |
| `POST /api/devices/{deviceID}/action/{actionName}` | Call action on given device |
| `DELETE /api/devices/action/{timestamp}/{id}` | Delete delayed action |
| `GET /api/devices/roles/{type}` | Get array of roles specified for device type |
| `POST /api/slave/{uuid}/api/devices/{deviceID}/action/{actionName}` | Call action using master as a proxy for slave |
| `GET /api/uiDeviceInfo` | Get device info |
| `GET /api/devices/hierarchy` | Get device type hierarchy |

### diagnostics

| Method and path | Summary |
|---|---|
| `GET /api/diagnostics` | Get diagnostics |
| `GET /api/apps/com.fibaro.zwave/diagnostics/transmissions` | Returns information about zwave transmissions |

### energy

| Method and path | Summary |
|---|---|
| `GET /api/energy/devices` | Energy devices info |
| `GET /api/energy/consumption/summary` | Summary of energy production/consumption |
| `GET /api/energy/consumption/metrics` | Metrics of energy production/consumption |
| `GET /api/energy/consumption/detail` | Details of energy production/consumption |
| `GET /api/energy/consumption/room/{roomId}/detail` | Details of energy production/consumption in room |
| `GET /api/energy/consumption/device/{deviceId}/detail` | Details of given device energy production/consumption in given periods of time |
| `GET /api/energy/billing/summary` | Summary of energy cost and consumption during current and last billing periods |
| `GET /api/energy/billing/periods` | List of billing periods |
| `POST /api/energy/billing/periods` | Sets new billing period |
| `GET /api/energy/billing/tariff` | Energy billing tariff |
| `PUT /api/energy/billing/tariff` | Changes energy tariff |
| `GET /api/energy/installationCost` | List of energy installation costs |
| `POST /api/energy/installationCost` | Creates installation cost |
| `GET /api/energy/installationCost/{id}` | Energy installation cost by id |
| `PUT /api/energy/installationCost/{id}` | Updates energy installation cost with given id. |
| `DELETE /api/energy/installationCost/{id}` | Deletes installation cost with given id. Main installation cost with id 1 cannot deleted. |
| `GET /api/energy/savings/detail` | Details of energy savings |
| `GET /api/energy/savings/summary` | Summary of energy savings |
| `GET /api/energy/savings/installation` | Energy savings data from beginning of installation |
| `GET /api/energy/ecology/summary` | Summary of energy ecology |
| `GET /api/energy/ecology/detail` | Details of energy ecology |
| `DELETE /api/energy/consumption` | Clears energy data. Clears all energy data when no parameters are passed. |
| `GET /api/energy/settings` | Energy related settings |
| `PUT /api/energy/settings` | Updates energy related settings |
| `GET /api/energy/datadump` | Dumps file containing all energy data stored in database on Home Center |

### events-history

| Method and path | Summary |
|---|---|
| `GET /api/events/history` | Retrieves list of events that match filters |
| `DELETE /api/events/history` | deletes events that fulfill conditions |
| `GET /api/events/dump` | Dumps file containing all history events stored in database on Home Center |

### events-publishevent-specificevents

| Method and path | Summary |
|---|---|
| `POST /api/events/publishEvent/{eventName}` | Publish event |
| `POST /api/events/publishEvent/GeofenceEvent` | Publish GeofenceEvent event |

### favoritecolors

| Method and path | Summary |
|---|---|
| `GET /api/panels/favoriteColors` | Get favorite colors |
| `POST /api/panels/favoriteColors` | Create favorite colors object |
| `PUT /api/panels/favoriteColors/{favoriteColorID}` | Modify favorite colors object |
| `DELETE /api/panels/favoriteColors/{favoriteColorID}` | Delete favorite colors |

### favoritecolorsv2

| Method and path | Summary |
|---|---|
| `GET /api/panels/favoriteColors/v2` | Get favorite colors |
| `POST /api/panels/favoriteColors/v2` | Create favorite colors object |
| `PUT /api/panels/favoriteColors/v2/{favoriteColorID}` | Modify favorite colors object |

### fibaro-json

| Method and path | Summary |
|---|---|
| `GET /fibaro/json/{parametersTemplate}.json` | Get device parameters template |

### firsttimeinitiation

| Method and path | Summary |
|---|---|
| `GET /api/fti/v2` | Get FTI model |
| `POST /api/fti/v2/changeStep/{step}` | Set current FTI step |
| `POST /api/fti/v2/finish` | Finish FTI |
| `POST /api/fti/v2/reset` | Reset FTI |

### gatewayconnection

| Method and path | Summary |
|---|---|
| `GET /api/service/discovery/resolve/{type}/{value}` | Gateway connection resolve |
| `GET /api/service/discovery/search` | Discovery search |
| `GET /api/service/resolve/{type}/{value}` | Discover gateway in the network by serial number or ip |
| `GET /api/service/gateway/role` | Gateway role |
| `PUT /api/service/gateway/role` | Switch role |
| `? /api/service/gateway/role/slave` | (defined in a referenced file) |
| `GET /api/service/slaves` | Get list of slaves |
| `POST /api/service/slaves` |  |
| `GET /api/service/slaves/{id}/password` | Slave login and password (Base64 encoded) |
| `PUT /api/service/slaves/{id}` | Replace slave |
| `DELETE /api/service/slaves/{id}` | Delete slave |
| `GET /api/service/slaves/{serialOrId}/ip` | Get slave IP address |
| `GET /api/remoteGateway/verifyGateway` | Verify the serial of given gateway |

### home

| Method and path | Summary |
|---|---|
| `GET /api/home` | Get home info |
| `PUT /api/home` | Update home info |

### icons

| Method and path | Summary |
|---|---|
| `GET /api/icons` | Get a list of all available icons |
| `POST /api/icons` | Upload icon |
| `DELETE /api/icons` | Delete icon |

### installer

| Method and path | Summary |
|---|---|
| `GET /api/installer` | Returns information about installer assigned to this HC gateway |
| `POST /api/installer` | Assigns installer to HC gateway |
| `PUT /api/installer` | Grants/revokes remote access from installer |
| `DELETE /api/installer` | Removes installer from this gateway |
| `POST /api/installer/monitoringRequest` | Initiates processing of insteller's monitoring request |
| `POST /api/installer/remoteAccessRequest` | Initiates processing of insteller's remote access request |
| `GET /api/installer/mobileDevicesToNotify` | Returns information about devices to notify |
| `PUT /api/installer/mobileDevicesToNotify` | Updates list of mobile devices that should be notified about installer requests |
| `PUT /api/installer/mobileDevicesToNotify/{deviceId}` | Adds mobile device that should be notified about installer requests |
| `DELETE /api/installer/mobileDevicesToNotify/{deviceId}` | Removes mobile device from the list of devices to notify |

### iosdevices

| Method and path | Summary |
|---|---|
| `GET /api/iosDevices` | Get a list of all available iosDevices |

### linkeddevices

| Method and path | Summary |
|---|---|
| `GET /api/linkedDevices/v1/devices` | Get information about linked devices |
| `POST /api/linkedDevices/v1/devices` | Create new linked device |
| `GET /api/linkedDevices/v1/providers` | Get linked devices providers list and information about available links |
| `GET /api/linkedDevices/v1/devices/{deviceID}` | Get information about linked device |
| `PUT /api/linkedDevices/v1/devices/{deviceID}` | Update linked device |
| `DELETE /api/linkedDevices/v1/devices/{deviceID}` | Delete existing linked device |
| `GET /api/linkedDevices/v1/inputDevices` | Get id list of all input devices |

### loginstatus

| Method and path | Summary |
|---|---|
| `GET /api/loginStatus` | Get login status |
| `POST /api/loginStatus` | Call login action |

### networkdiscovery

| Method and path | Summary |
|---|---|
| `POST /api/networkDiscovery/arp` | Network Discovery |

### nice-elero

| Method and path | Summary |
|---|---|
| `? /api/nice/bind` | (defined in a referenced file) |
| `? /api/nice/bind/{nice_id}` | (defined in a referenced file) |
| `? /api/nice/bind/mono/options` | (defined in a referenced file) |
| `? /api/nice/bind/protocol` | (defined in a referenced file) |
| `? /api/nice/bind/abort` | (defined in a referenced file) |
| `? /api/nice/devices/{nice_id}` | (defined in a referenced file) |
| `? /api/nice/devices/{nice_id}/synchronize` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/nice/devices/{nice_id}/synchronize` | (defined in a referenced file) |
| `? /api/nice/devices/synchronize_all` | (defined in a referenced file) |
| `? /api/nice/mono` | (defined in a referenced file) |
| `? /api/nice/enable_spontaneous` | (defined in a referenced file) |
| `? /api/nice/radio_reset` | (defined in a referenced file) |
| `? /api/nice/network_reset` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/nice/network_reset` | (defined in a referenced file) |
| `? /api/nice/background_polling` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/nice/background_polling` | (defined in a referenced file) |
| `? /api/nice/configuration/parameters/{nice_id}` | (defined in a referenced file) |
| `? /api/nice/configuration/parameters/{nice_id}/default` | (defined in a referenced file) |
| `? /api/nice/configuration/parameters/{nice_id}/{number}` | (defined in a referenced file) |
| `? /api/nice/configuration/parameters/{nice_id}/{number}/default` | (defined in a referenced file) |
| `? /api/nice/polling/configuration/{nice_id}/{number}` | (defined in a referenced file) |
| `? /api/nice/mailbox/{nice_id}/configuration_parameters` | (defined in a referenced file) |
| `? /api/nice/polling` | (defined in a referenced file) |
| `? /api/nice/polling/{nice_id}` | (defined in a referenced file) |
| `? /api/nice/favorite_position/set` | (defined in a referenced file) |
| `? /api/nice/favorite_position/move` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/nice/favorite_position/set` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/nice/favorite_position/move` | (defined in a referenced file) |
| `? /api/nice/pending_actions/{action_id}` | (defined in a referenced file) |
| `? /api/nice/next_solar_report/{nice_id}` | (defined in a referenced file) |
| `? /api/elero/bind` | (defined in a referenced file) |
| `? /api/elero/bind/abort` | (defined in a referenced file) |
| `? /api/elero/bind/synchronous` | (defined in a referenced file) |
| `? /api/elero/network_reset` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/network_reset` | (defined in a referenced file) |
| `? /api/elero/background_polling` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/background_polling` | (defined in a referenced file) |
| `? /api/elero/polling` | (defined in a referenced file) |
| `? /api/elero/polling/{nice_id}` | (defined in a referenced file) |
| `? /api/elero/favorite_position/prepare` | (defined in a referenced file) |
| `? /api/elero/favorite_position/start` | (defined in a referenced file) |
| `? /api/elero/favorite_position/set` | (defined in a referenced file) |
| `? /api/elero/favorite_position/clear` | (defined in a referenced file) |
| `? /api/elero/favorite_position/move` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/favorite_position/prepare` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/favorite_position/start` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/favorite_position/set` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/favorite_position/clear` | (defined in a referenced file) |
| `? /api/slave/{uuid}/api/elero/favorite_position/move` | (defined in a referenced file) |
| `? /api/elero/device/{nice_id}/send_key` | (defined in a referenced file) |

### notificationcenter

| Method and path | Summary |
|---|---|
| `GET /api/notificationCenter` | Notification list |
| `POST /api/notificationCenter` | Create notification |
| `DELETE /api/notificationCenter` | Delete notifications |
| `GET /api/notificationCenter/{notificationId}` | Notification |
| `PUT /api/notificationCenter/{notificationId}` | Edit notification |
| `DELETE /api/notificationCenter/{notificationId}` | Delete notification |
| `POST /api/notificationCenter/markAsRead` | Notification list |
| `POST /api/notificationCenter/markAsUnread` | Mark notification as unread |

### panels-climate

| Method and path | Summary |
|---|---|
| `GET /api/panels/climate` | Get a list of all available climate zones |
| `POST /api/panels/climate` | Create climate zone |
| `GET /api/panels/climate/{climateID}` | Get specific climate zone |
| `PUT /api/panels/climate/{climateID}` | Modify specific climate zone |
| `DELETE /api/panels/climate/{climateID}` | Delete specific climate zone |
| `POST /api/panels/climate/action/createDefaultZones` | Create climate default zones |
| `GET /api/panels/climate/availableDevices` | Get a list of all available climate devices |

### panels-customevents

| Method and path | Summary |
|---|---|
| `GET /api/customEvents` | Get a list of all defined custom events |
| `POST /api/customEvents` | Create custom event |
| `GET /api/customEvents/{customEventName}` | Get custom event with provided name |
| `POST /api/customEvents/{customEventName}` | Emit custom event |
| `PUT /api/customEvents/{customEventName}` | Modify custom event |
| `DELETE /api/customEvents/{customEventName}` | Delete custom event |
| `GET /api/customEvents/{customEventName}/publish` | Emit custom event |

### panels-family

| Method and path | Summary |
|---|---|
| `GET /api/panels/family` | Get users family |

### panels-globalvariables

| Method and path | Summary |
|---|---|
| `GET /api/globalVariables` | Get a list of all available global variables |
| `POST /api/globalVariables` | Create global variable |
| `GET /api/globalVariables/{globalVariableName}` | Get global variable |
| `PUT /api/globalVariables/{globalVariableName}` | Modify global variable |
| `DELETE /api/globalVariables/{globalVariableName}` | Delete global variable |

### panels-humidity

| Method and path | Summary |
|---|---|
| `GET /api/panels/humidity` | Get a list of all available humidity objects |
| `POST /api/panels/humidity` | Create humidity |
| `GET /api/panels/humidity/{humidityID}` | Get humidity object |
| `PUT /api/panels/humidity/{humidityID}` | Modify humidity |
| `DELETE /api/panels/humidity/{humidityID}` | Delete humidity |

### panels-location

| Method and path | Summary |
|---|---|
| `GET /api/panels/location` | Get a list of all available locations |
| `POST /api/panels/location` | Create location |
| `GET /api/panels/location/{locationID}` | Get location |
| `PUT /api/panels/location/{locationID}` | Modify location |
| `DELETE /api/panels/location/{locationID}` | Delete location |

### panels-notifications

| Method and path | Summary |
|---|---|
| `GET /api/panels/notifications` | Get a list of all available notifications |
| `POST /api/panels/notifications` | Create notification |
| `GET /api/panels/notifications/{notificationID}` | Get notification |
| `PUT /api/panels/notifications/{notificationID}` | Modify notification |
| `DELETE /api/panels/notifications/{notificationID}` | Delete notification |

### panels-sprinklers

| Method and path | Summary |
|---|---|
| `GET /api/panels/sprinklers` | Get all available sprinkler schedules |
| `POST /api/panels/sprinklers` | Creates new sprinkler schedule |
| `GET /api/panels/sprinklers/{scheduleId}` | Get specific sprinkler schedule |
| `PUT /api/panels/sprinklers/{scheduleId}` | Update specific sprinkler schedule |
| `DELETE /api/panels/sprinklers/{scheduleId}` | Removes specific sprinkler schedule |
| `POST /api/panels/sprinklers/{scheduleId}/sequences` | Create new sprinkler sequence |
| `PUT /api/panels/sprinklers/{scheduleId}/sequences/{sequenceId}` | Update specific sprinkler sequence |
| `DELETE /api/panels/sprinklers/{scheduleId}/sequences/{sequenceId}` | Removes specific sprinkler sequence from schedule |
| `POST /api/panels/sprinklers/{scheduleId}/sequences/{sequenceId}/startWatering` | Start given sequence |
| `POST /api/panels/sprinklers/{scheduleId}/sequences/{sequenceId}/stopWatering` | Stop given sequence |

### panelservice

| Method and path | Summary |
|---|---|
| `POST /api/panelService/1/action/startUpgrade` | Start upgrade zwave device |
| `POST /api/panelService/1/action/abortUpgrade` | Abort upgrade zwave device |
| `POST /api/panelService/1/action/checkUpgradeAvailability` | Check upgrade availability for zwave device |
| `POST /api/panelService/1/action/changelog` | Get zwave device changelog |

### passwordforgotten

| Method and path | Summary |
|---|---|
| `GET /api/passwordForgotten` | Password Forgotten |
| `GET /api/passwordForgotten/requestReset` | Request Password Reset |
| `GET /api/passwordForgotten/reset` | Reset Password |

### profiles

| Method and path | Summary |
|---|---|
| `GET /api/profiles` | Get all profiles and active profile |
| `POST /api/profiles` | Create new profile with provided name |
| `PUT /api/profiles` | Update profiles and set active profile |
| `GET /api/profiles/{profileId}` | Get profile |
| `PUT /api/profiles/{profileId}` | Update existing profile |
| `DELETE /api/profiles/{profileId}` | Remove existing profile |
| `PUT /api/profiles/{profileId}/partitions/{partitionId}` | Update profile partition action |
| `PUT /api/profiles/{profileId}/climateZones/{zoneId}` | Update profile climate zone action |
| `PUT /api/profiles/{profileId}/scenes/{sceneId}` | Update profile scene actor |
| `POST /api/profiles/reset` | Rest profiles model to default value |
| `POST /api/profiles/activeProfile/{profileId}` | Set active profile |

### reboot

| Method and path | Summary |
|---|---|
| `POST /api/service/reboot` | Reboot device |

### refreshstates

| Method and path | Summary |
|---|---|
| `GET /api/refreshStates` | Refresh sates |

### rgbprograms

| Method and path | Summary |
|---|---|
| `GET /api/RGBPrograms` | Get a list of all available RGB programs |
| `POST /api/RGBPrograms` | Create RGB program |
| `GET /api/RGBPrograms/{programID}` | Get RGB program object |
| `PUT /api/RGBPrograms/{programID}` | Modify RGB program |
| `DELETE /api/RGBPrograms/{programID}` | Delete RGB program |

### rooms

| Method and path | Summary |
|---|---|
| `GET /api/rooms` | Get a list of all available rooms |
| `POST /api/rooms` | Create room |
| `GET /api/rooms/{roomID}` | Get room object |
| `PUT /api/rooms/{roomID}` | Modify room |
| `DELETE /api/rooms/{roomID}` | Delete room |
| `POST /api/rooms/{roomID}/action/setAsDefault` | Sets as default room in system |
| `POST /api/rooms/{roomID}/groupAssignment` | Assigns roomID to all entities given in a body |

### scenes

| Method and path | Summary |
|---|---|
| `GET /api/scenes` | Get a list of all available scenes |
| `POST /api/scenes` | Create scene |
| `POST /api/scenes/hasTriggers` | Filter scenes by triggers |
| `GET /api/scenes/{sceneID}` | Get scene object |
| `PUT /api/scenes/{sceneID}` | Modify scene |
| `DELETE /api/scenes/{sceneID}` | Delete scene |
| `GET /api/scenes/{sceneID}/execute` | Executes asynchronously executive part of the scene neglecting conditional part. |
| `POST /api/scenes/{sceneID}/execute` | Executes asynchronously executive part of the scene neglecting conditional part. |
| `GET /api/scenes/{sceneID}/executeSync` | Executes synchronously executive part of the scene neglecting conditional part. |
| `POST /api/scenes/{sceneID}/executeSync` | Executes synchronously executive part of the scene neglecting conditional part. |
| `POST /api/scenes/{sceneID}/convert` | Convert block scene to lua. |
| `POST /api/scenes/{sceneID}/copy` | Create scene copy. |
| `POST /api/scenes/{sceneID}/copyAndConvert` | Copy and convert block scene to lua. |
| `GET /api/scenes/{sceneID}/kill` | Kill running scene. |
| `POST /api/scenes/{sceneID}/kill` | Kill running scene. |

### sections

| Method and path | Summary |
|---|---|
| `GET /api/sections` | Get list of all available sections |
| `POST /api/sections` | Create section |
| `GET /api/sections/{sectionID}` | Get section object |
| `PUT /api/sections/{sectionID}` | Modify section |
| `DELETE /api/sections/{sectionID}` | Delete section |

### service-actions

| Method and path | Summary |
|---|---|
| `GET /api/service/actions` | Get list of actions and information about them performed on HC. |
| `GET /api/service/actions/{id}` | Get information about action with given ID. |

### service-backups

| Method and path | Summary |
|---|---|
| `GET /api/service/canCreateBackups` | Checks if backups are possible |
| `GET /api/service/getLocalBackupsStatus` | Checks if local backups create and restore are possible |
| `GET /api/service/getRemoteBackupsStatus` | Checks if remote backups create and restore are possible |
| `GET /api/service/backups` | Get current backup settings |
| `POST /api/service/backups` | Create backup |
| `DELETE /api/service/backups` | Removes backup |
| `DELETE /api/service/backups/{id}` | Removes backup |

### service-update

| Method and path | Summary |
|---|---|
| `GET /api/update` | Get list of updates and information about them. |
| `POST /api/service/checkUpdate` | Start asynchronous update availability checking |
| `POST /api/service/update` | Create/Post an action related to update. |
| `DELETE /api/service/update` | Remove downloaded update from HC |

### settings-info

| Method and path | Summary |
|---|---|
| `GET /api/settings/info` | Get current info settings |
| `PUT /api/settings/info` | Modify current info settings |
| `GET /api/settings/info/configurationData` | Download system configuration |

### settings-led

| Method and path | Summary |
|---|---|
| `GET /api/settings/led` | Get Home Center LED brightness |
| `PUT /api/settings/led` | Modify current Home Center LED brightness |

### settings-location

| Method and path | Summary |
|---|---|
| `GET /api/settings/location` | Get current location |
| `PUT /api/settings/location` | Modify current location. |

### settings-network

| Method and path | Summary |
|---|---|
| `GET /api/settings/network` | Get network configuration |
| `GET /api/settings/network/connectivity` | Get Internet connectivity status |
| `GET /api/settings/network/radio` | Get radio configuration |
| `PUT /api/settings/network/radio` | Update radio configuration |
| `GET /api/settings/network/radio/{radioType}` | Get radio configuration by device type |
| `PUT /api/settings/network/radio/{radioType}` | Update radio configuration by device type |
| `GET /api/settings/network/interfaces` | Get list of network interfaces |
| `GET /api/settings/network/interfaces/{interfaceName}` | Get interface configuration |
| `PUT /api/settings/network/interfaces/{interfaceName}` | Update interface configuration |
| `GET /api/settings/network/interfaces/{interfaceName}/apList` | Get list of APs |
| `GET /api/settings/network/interfaces/{interfaceName}/apInfo` | Get list of APs with additional information |
| `GET /api/settings/network/connections` | Get list of network connections |
| `POST /api/settings/network/connections` | Add a new connection |
| `GET /api/settings/network/connections/{connectionUuid}` | Get connection status |
| `PUT /api/settings/network/connections/{connectionUuid}` | Update the network connection |
| `DELETE /api/settings/network/connections/{connectionUuid}` | Remove the network connection |
| `POST /api/settings/network/connections/{connectionUuid}/check` | Check the connection status |
| `POST /api/settings/network/connections/{connectionUuid}/connect` | Connect to the wireless network |
| `POST /api/settings/network/connections/{connectionUuid}/disconnect` | Disconnect from the wireless network |
| `PUT /api/settings/network/resetInterfaces` | Reset network interfaces configuration |
| `GET /api/settings/network/AccessPointMode` | Get AccessPoint status |
| `PUT /api/settings/network/AccessPointMode` | Set AccessPoint mode |
| `GET /api/settings/network/enabledProtocols` | Get enabled protocols |
| `PUT /api/settings/network/enabledProtocols` | Set enabled protocols |
| `GET /api/settings/remoteAccess/status` | Get all remote access statuses |
| `GET /api/settings/remoteAccess/status/{typeName}` | Get remote access type state |
| `PUT /api/settings/remoteAccess/status/{typeName}` | Set remote access type state |
| `PUT /api/service/remoteAccess/status/{typeName}` | Set remote access type state |
| `GET /api/settings/certificates/ca` | Get the Root CA certificate |

### sortorder

| Method and path | Summary |
|---|---|
| `POST /api/sortOrder` | Update sort order |
| `POST /api/sortOrder/syncUsersWithAdmin` | Synchronize sort order for all users based on admin |

### systemstatus

| Method and path | Summary |
|---|---|
| `GET /api/service/systemStatus` | System status |
| `POST /api/service/systemStatus` | Set system status |
| `POST /api/service/restartServices` | Clear error |

### useractivity

| Method and path | Summary |
|---|---|
| `GET /api/userActivity` | Get user activity list |

### users

| Method and path | Summary |
|---|---|
| `GET /api/users` | Get a list of available users |
| `POST /api/users` | Create User |
| `GET /api/users/{userID}` | Get user object |
| `PUT /api/users/{userID}` | Modify user |
| `DELETE /api/users/{userID}` | Delete user |
| `POST /api/users/{userID}/raInvite` | User invitation |
| `POST /api/users/action/changeAdmin/{newAdminId}` | Initiates transfer of administrator role to {newAdminId} |
| `POST /api/users/action/confirmAdminTransfer` | Confirms pending admin role transfer. Only user that is target for admin role may call this endpoint successfully |
| `POST /api/users/action/cancelAdminTransfer` | Cancels pending admin role transfer. Only current superuser may call this endpoint successfully |
| `POST /api/users/action/synchronize` | Users synchronization |
| `POST /api/users/action/setPassword` | Set user password using one-time code for authorization |

### voip

| Method and path | Summary |
|---|---|
| `GET /api/voip` | Get list of all available voip devices |

### weather

| Method and path | Summary |
|---|---|
| `GET /api/weather` | Get weather object |

### zigbee-engine-api

| Method and path | Summary |
|---|---|
| `GET /api/zigbee/network` | Get network parameters |
| `GET /api/zigbee/permit` | Devices joining state |
| `POST /api/zigbee/permit` | Permit join |
| `DELETE /api/zigbee/permit` | Disallow join |
| `GET /api/zigbee/devices` | Get all devices in network |
| `GET /api/zigbee/devices/{ieeeAddr}` | Get device |
| `DELETE /api/zigbee/devices/{ieeeAddr}` | Remove device from network |
| `GET /api/zigbee/devices/{ieeeAddr}/get` | Get from device |
| `POST /api/zigbee/devices/{ieeeAddr}/set` | Set on device |
| `DELETE /api/zigbee/hc/devices` | Remove HC device from network |

### zwave-associations

| Method and path | Summary |
|---|---|
| `GET /api/apps/com.fibaro.zwave/nodes/{nodeId}/associationGroupInfo` | Returns static information about association groups for given nodeId. |
| `GET /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/associationGroupInfo` | Use proxy to returns static information about association groups for given nodeId. |
| `GET /api/apps/com.fibaro.zwave/nodes/{nodeId}/endpoints/{endpointId}/associationGroupInfo` | Returns static information about association groups for given {nodeId, endpointId} |
| `GET /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/endpoints/{endpointId}/associationGroupInfo` | Use proxy to return static information about association groups for given {nodeId, endpointId} |
| `GET /api/apps/com.fibaro.zwave/nodes/{nodeId}/associations` | Returns all associations for given nodeId |
| `GET /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/associations` | Use proxy to return all associations for given nodeId |
| `GET /api/apps/com.fibaro.zwave/nodes/{nodeId}/endpoints/{endpointId}/associations` | Returns all associations for given {nodeId, endpointId} |
| `GET /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/endpoints/{endpointId}/associations` | Use proxy to return all associations for given {nodeId, endpointId} |
| `GET /api/apps/com.fibaro.zwave/nodes/{nodeId}/actions` | Returns information for whole actions |
| `POST /api/apps/com.fibaro.zwave/nodes/{nodeId}/actions` | Performs action for given nodeId |
| `GET /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/actions` | Returns information for whole proxy actions |
| `POST /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/actions` | Performs proxy action for given nodeId |
| `GET /api/apps/com.fibaro.zwave/nodes/{nodeId}/actions/{actionId}` | Returns information for given action |
| `DELETE /api/apps/com.fibaro.zwave/nodes/{nodeId}/actions/{actionId}` | Removes (cancels) given action |
| `GET /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/actions/{actionId}` | Returns information for given proxy action |
| `DELETE /api/slave/{uuid}/api/apps/com.fibaro.zwave/nodes/{nodeId}/actions/{actionId}` | Removes (cancels) given proxy action |

### zwave

| Method and path | Summary |
|---|---|
| `GET /api/zwaveSettings` | Get zwave settings object |
| `PUT /api/zwaveSettings` | Update zwave settings data |
| `GET /api/slave/{uuid}/api/zwaveSettings` | Use proxy to get zwave settings object |
| `PUT /api/slave/{uuid}/api/zwaveSettings` | Use proxy to update zwave settings data |
| `POST /api/slave/{uuid}/api/zwave/factory_reset` | Perform Factory Reset on slave |
| `GET /api/zwaveReconfigurationTasks` | Get zwave configuration task list |
| `POST /api/zwaveReconfigurationTasks` | Start device configuration |
| `GET /api/zwaveReconfigurationTasks/{taskId}` | Get zwave configuration task |
| `PUT /api/zwaveReconfigurationTasks/{taskId}` | Update zwave configuration task |
| `DELETE /api/zwaveReconfigurationTasks/{taskId}` | Delete zwave configuration task |
| `POST /api/zwaveReconfigurationTasks/reconfigureAll` | Start configure zwave network |
