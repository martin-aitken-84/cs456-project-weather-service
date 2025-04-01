# from dataclasses import dataclass, asdict
# from datetime import datetime
# import configparser
# import logging
# import time
# import requests
# import pandas as pd
# import os




# @dataclass
# class Measurement:
#     time_stamp: str = None
#     temperature: float = None
#     wind_direction: str = None
#     wind_speed: float = None
#     humidity: float = None


# def measurement(df, row_num):
#     time_now = datetime.now()
#     time_now = time_now.isoformat()
    
#     temperature = float(df.iloc[row_num][2])
#     wind_direction = str(df.iloc[row_num][3]).strip()
#     wind_speed = float(df.iloc[row_num][4])
#     # Avoid negative wind speeds.
#     if wind_speed < 0:
#         wind_speed = 0
#     humidity = float(df.iloc[row_num][6])

#     return Measurement(
#         time_stamp=time_now,
#         temperature=temperature,
#         wind_direction=wind_direction,
#         wind_speed=wind_speed,
#         humidity=humidity
#     )


# def load_data(file_name) -> pd.DataFrame:
#     # Read Excel file into DataFrame
#     df = pd.read_excel(file_name, sheet_name='Data') 
#     return df


# def load_config(file_name):
#     if not os.path.isfile(file_name):
#         raise FileNotFoundError(f"Cannot find configuration file \ {file_name} \.")

#     config = configparser.ConfigParser()
#     config.read(file_name)
#     return config
    

# def read_settings(config):
#     settings = {}
#     settings['url'] = config['connection_settings']['url']
#     settings['file_name'] = config['file_settings']['file_name']
#     settings['excel_file'] = config['file_settings']['excel_file']
#     settings['sheet_name'] = config['file_settings']['sheet_name']
#     settings['serial_number'] = config['station_settings']['serial_number']
#     settings['sample_period'] = config['station_settings']['sample_period']

#     if len(settings['serial_number']) == 0:
#         logging.error("serial_number cannot be an empty string.")
#         return None
#     return settings


# def post_measurements(settings: dict, df) -> None:
#     # A function to post a weather station measurement to a remote URL.
#     x = 0
    
#     while True:
#         sleep_time = settings["sample_period"]
#         new_measurement = measurement(df, x)
#         new_measurement = asdict(new_measurement)
#         x += 1

#         try:
#             url = settings["url"]
#             json = new_measurement
#             params = settings["serial_number"]
#             response = requests.post(settings["url"],json=new_measurement, params={"serial_number": settings["serial_number"]})
            
#             if response.status_code != 201:
#                 logging.error(f"Web service returned {response.status_code} instead of 201.")

#         except requests.exceptions.RequestException as e:
#             logging.error(e)
#             time.sleep(10)


# __shutdown__: bool = False


# def main():
#     global __shutdown__
#     config = load_config('solution\WeatherSvc\config.ini')
#     settings = read_settings(config)
#     if settings is None:
#         return

#     df = load_data(settings["excel_file"])
#     post_measurements(settings, df)
