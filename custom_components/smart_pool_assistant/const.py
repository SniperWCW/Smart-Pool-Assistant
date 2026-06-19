DOMAIN = "smart_pool_assistant"

CONF_API_KEY = "api_key"
CONF_BLE_ADDRESS = "ble_address"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_CHLOR_SENSOR = "chlor_sensor"
CONF_PH_SENSOR = "ph_sensor"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_POOL_VOLUME = "pool_volume"
CONF_CHLOR_TARGET = "chlor_target"
CONF_PH_TARGET = "ph_target"
CONF_CHLOR_CONTENT = "chlor_content" # Wirkstoffanteil (z.B. 0.56)
CONF_PH_DOWN_DOSAGE = "ph_down_dosage" # ml pro 10m3 für 0.2 pH
CONF_PH_UP_DOSAGE = "ph_up_dosage"     # g pro 10m3 für 0.1 pH
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_SERVICE_2 = "notify_service_2"
CONF_PERSISTENT_NOTIFICATION = "persistent_notification"
CONF_FOLLOW_UP_TIME = "follow_up_time"

# Filter Maintenance
CONF_FILTER_CLEAN_INTERVAL = "filter_clean_interval" # Days
CONF_FILTER_REPLACE_INTERVAL = "filter_replace_interval" # Days
CONF_FILTER_CLEAN_YELLOW_THRESHOLD = "filter_clean_yellow_threshold" # Days before interval
CONF_FILTER_CLEAN_RED_THRESHOLD = "filter_clean_red_threshold" # Days before interval
CONF_FILTER_REPLACE_YELLOW_THRESHOLD = "filter_replace_yellow_threshold" # Days before interval
CONF_FILTER_REPLACE_RED_THRESHOLD = "filter_replace_red_threshold" # Days before interval
CONF_WEATHER_ENTITY = "weather_entity"
