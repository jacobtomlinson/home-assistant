"""
Support for Met Office Datapoint weather service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.datapoint/
"""
import logging
from datetime import timedelta

from homeassistant.const import CONF_API_KEY, TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

REQUIREMENTS = ['datapoint==0.4.0']
_LOGGER = logging.getLogger(__name__)

# Sensor types are defined like so:
# Name, si unit, us unit, ca unit, uk unit, uk2 unit
SENSOR_TYPES = {
    'summary': ['Summary', None, None, None, None, None],
    'icon': ['Icon', None, None, None, None, None],
    'precip_probability': ['Precip Probability', '%', '%', '%', '%', '%'],
    'temperature': ['Temperature', '°C', '°F', '°C', '°C', '°C'],
    'feels_like_temperature': ['Feels Like Temperature',
                             '°C', '°F', '°C', '°C', '°C'],
    'wind_speed': ['Wind Speed', 'm/s', 'mph', 'km/h', 'mph', 'mph'],
    'wind_gust': ['Wind Gust', 'm/s', 'mph', 'km/h', 'mph', 'mph'],
    'wind_direction': ['Wind Direction', '°', '°', '°', '°', '°'],
    'humidity': ['Humidity', '%', '%', '%', '%', '%'],
    'visibility': ['Visibility', 'km', 'm', 'km', 'km', 'm'],
}

# Return cached results if last scan was less then this time ago.
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Forecast.io sensor."""
    import datapoint

    if None in (hass.config.latitude, hass.config.longitude):
        _LOGGER.error("Latitude or longitude not set in Home Assistant config")
        return False

    try:
        conn = datapoint.connection(api_key=config.get(CONF_API_KEY, None))
        site = conn.get_nearest_site(hass.config.longitude, hass.config.latitude)
        forecast = conn.get_forecast_for_site(site.id, "3hourly")
        forecast.now()
    except ValueError:
        _LOGGER.error(
            "Connection error "
            "Please check your settings for Met Office Datapoint.")
        return False

    data = ForeCastData(config.get(CONF_API_KEY, None),
                        hass.config.latitude,
                        hass.config.longitude)

    dev = []
    for variable in config['monitored_conditions']:
        if variable not in SENSOR_TYPES:
            _LOGGER.error('Sensor type: "%s" does not exist', variable)
        else:
            dev.append(ForeCastSensor(data, variable))

    add_devices(dev)


# pylint: disable=too-few-public-methods
class ForeCastSensor(Entity):
    """Implementation of a Met Office Datapoint sensor."""

    def __init__(self, weather_data, sensor_type):
        """Initialize the sensor."""
        self.client_name = 'Weather'
        self._name = SENSOR_TYPES[sensor_type][0]
        self.forecast_client = weather_data
        self.type = sensor_type
        self._state = None
        self._unit_of_measurement = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self.client_name, self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    # pylint: disable=too-many-branches,too-many-statements
    def update(self):
        """Get the latest data from Met Office Datapoint and updates the states."""
        self.forecast_client.update()
        data = self.forecast_client.data

        try:
            if self.type == 'summary':
                self._state = data.weather.text
                self._unit_of_measurement = data.weather.units
            elif self.type == 'icon':
                self._state = data.weather.value
                self._unit_of_measurement = data.weather.units
            elif self.type == 'precip_probability':
                self._state = round(data.precipitation.value * 100, 1)
                self._unit_of_measurement = data.precipitation.units
            elif self.type == 'temperature':
                self._state = round(data.temperature.value, 1)
                self._unit_of_measurement = data.temperature.units
            elif self.type == 'feels_like_temperature':
                self._state = round(data.feels_like_temperature.value, 1)
                self._unit_of_measurement = data.feels_like_temperature.units
            elif self.type == 'wind_speed':
                self._state = data.wind_speed.value
                self._unit_of_measurement = data.wind_speed.units
            elif self.type == 'wind_gust':
                self._state = data.wind_gust.value
                self._unit_of_measurement = data.wind_gust.units
            elif self.type == 'wind_direction':
                self._state = data.wind_direction.value
                self._unit_of_measurement = data.wind_direction.units
            elif self.type == 'humidity':
                self._state = round(data.humidity.value * 100, 1)
                self._unit_of_measurement = data.humidity.units
            elif self.type == 'visibility':
                self._state = data.visibility.value
                self._unit_of_measurement = data.visibility.units

        except:
            pass


class ForeCastData(object):
    """Gets the latest data from Met Office Datapoint."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, api_key, latitude, longitude):
        """Initialize the data object."""
        self._api_key = api_key
        self.latitude = latitude
        self.longitude = longitude

        self.data = None

        self.update()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from Met Office Datapoint."""
        import datapoint
        conn = datapoint.connection(api_key=self._api_key)
        site = conn.get_nearest_site(self.longitude, self.latitude)
        forecast = conn.get_forecast_for_site(site.id, "3hourly")
        self.data = forecast.now()
