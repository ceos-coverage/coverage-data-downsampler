import os

APP_CONFIG = {
    'SOLR_URL': "https://oiip.jpl.nasa.gov/solr/",
    'OUTPUT_DIR': os.path.abspath('/oiip-cached-data'),
    'DEFAULT_TARGET': 20000,
    'NO_DECIMATION_TARGET': -1,
    'DEFAULT_KEYS': [
        "measurement_date_time",
        "depth"
    ],
    'NO_MOD_KEYS': [
        "measurement_date_time",
        "depth",
        "lon",
        "lat"
    ],
    'AVAILABLE_FORMATS': {
        "csv": "text/csv",
        "json": "application/json"
    },
    'DEFAULT_FORMAT': "text/csv",
    'CACHE_FILES': True
}