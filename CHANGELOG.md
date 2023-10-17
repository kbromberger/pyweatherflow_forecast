## Release 0.6.4

**Date**: `NOT RELEASED`

### Changes

- Added new sensor `Power Save Mode` that shows the Power Mode of a Tempest device. Attributes of the sensor gives a textual explanation. For more information [read here](https://help.weatherflow.com/hc/en-us/articles/360048877194-Solar-Power-Rechargeable-Battery)

## Release 0.6.3

**Date**: `2023-10-17`

### Changes

- Added check for None values in all calculated sensors, to ensure they will not throw an error.

## Release 0.6.2

**Date**: `2023-10-15`

### Changes

- Ensuring that the sensor function still works with AIR and SKY devices, even though we do not add Voltage and battery values.

## Release 0.6.1

**Date**: `2023-10-15`

### Changes

- Optimizing the *Fetch Sensor Data* by removing 1 call to the API per cycle.

## Release 0.6.0

**Date**: `2023-10-14`

### Changes

- Rewritten the Request modules to simplify code base.
- Merged all API request needed for getting sensor data, into one function.

## Release 0.5.1

**Date**: `2023-10-13`

### Changes

- Fixing loop when retreiving device information - used for the voltage data.

## Release 0.5.0

**Date**: `2023-10-12`

### Changes

- Added Voltage sensor. This will only be available for Tempest devices. AIR and SKY will not be supported-
- Added calculated battery sensor, that show the % full. Calculated sensor based on the voltage value.


## Release 0.4.7

**Date**: `2023-10-09`

### Changes

- Fix wrong value in Absolute Humidity
- Added Beaufort sensor
- Added Freezing Altitude sensor