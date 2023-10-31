import os , tempfile
def get_settings():

    setting=  {
    'DRIVER_PATH':  "",
    'DRIVER_PROVIDER':  None,
    'DEBUG':  False,
    'FLASK_PROFILE':  False,
    'XRAY_PROFILE':  False,
    'LOGLEVEL':  "warning",
    'RASTER_CACHE_SIZE':  1024 * 1024 * 490 , 
    'RASTER_CACHE_COMPRESS_LEVEL':  9,
    'DEFAULT_TILE_SIZE': (256, 256),
    'LAZY_LOADING_MAX_SHAPE': (1024, 1024),
    'PNG_COMPRESS_LEVEL': 1,
    'DB_CONNECTION_TIMEOUT':  10,
    'REMOTE_DB_CACHE_DIR': os.path.join(tempfile.gettempdir(), "b3d"),
    'REMOTE_DB_CACHE_TTL':10 * 60 ,
    'RESAMPLING_METHOD':  "average",
    'REPROJECTION_METHOD': "linear",
    'ALLOWED_ORIGINS_METADATA':  ["*"],
    'ALLOWED_ORIGINS_TILES': ["*"],
    'SQL_USER':  None,
    'SQL_PASSWORD':  None,
    'MYSQL_USER': None,
    'MYSQL_PASSWORD': None,
    'POSTGRESQL_USER': None,
    'POSTGRESQL_PASSWORD':  None,
    'USE_MULTIPROCESSING':True,
    'MAX_POST_METADATA_KEYS':100
    }

    return setting
