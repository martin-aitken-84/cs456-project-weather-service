from flask import Flask, make_response, jsonify, request
import sqlalchemy
from sqlalchemy import select, insert, delete, create_engine, exc, Column, ForeignKey, Integer, CHAR, DateTime, Float
from sqlalchemy.orm import Session, declarative_base, relationship
import logging
import configparser
import os
import pandas as pd

Base = declarative_base()


class Station(Base):
    __tablename__ = 'stations'
    station_id = Column(Integer, primary_key=True, nullable=False)
    station_serial = Column(CHAR(25), nullable=False, unique=True)

    def __init__(self, station_serial) -> None:
        self.station_serial = station_serial

    def to_dict(self) -> dict:
        return {
            "station_id": self.station_id,
            "station_serial":self.station_serial
        }

    def __repr__(self):
        return f"\"Station({self.station_id}, {self.station_serial})"


class Direction(Base):
    __tablename__ = 'directions'
    direction_id = Column(Integer, primary_key=True, nullable=False)
    direction_name = Column(CHAR(4), nullable=False, unique=True)

    def __init__(self, direction_name) -> None:
        self.direction_name = direction_name

    def to_dict(self) -> dict:
        return {
            "direction_id": self.direction_id,
            "direction_name":self.direction_name
        }

    def __repr__(self):
        return f'Direction({self.direction_id}, {self.direction_name})'


class Measurement(Base):
    __tablename__ = 'measurements'
    measurement_id = Column(Integer, primary_key=True, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    time_stamp = Column(DateTime, nullable=False)
    temperature = Column(Float, nullable=False)
    direction_id = Column(Integer, ForeignKey("directions.direction_id"), nullable=True)
    wind_speed = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    station = relationship("Station")
    direction = relationship("Direction")

    def __init__(self, station_id, time_stamp, temperature, direction_id, wind_speed, humidity ) -> None:
        self.station_id = station_id
        self.time_stamp = time_stamp
        self.temperature = temperature
        self.direction_id = direction_id
        self.wind_speed = wind_speed
        self.humidity = humidity
        
    def to_dict(self) -> dict:
        return {
            "measurement_id": self.measurement_id,
            "station_id":self.station_id,
            "time_stamp":self.time_stamp,
            "temperature":self.temperature,
            "direction_id":self.direction_id,
            "wind_speed":self.wind_speed,
            "humidity":self.humidity
        }   

    def __repr__(self):
        return f"Measurement({self.measurement_id},{self.station_id},{self.time_stamp},{self.temperature},{self.direction_id},{self.wind_speed},{self.humidity})"


def mysql_engine(config_file: str) -> sqlalchemy.engine.Engine:
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Cannot find configuration file \ {config_file} \.")

    # Get database connection parameters from environment variables
    config = configparser.ConfigParser()
    config.read(config_file)
    connection_string = ""
    connection_args = {}
    try:
        connection_string = sqlalchemy.engine.url.URL.create(
            drivername=config['dbconnection']['drivername'],
            username=config['dbconnection']['DB_USER'],
            password=config['dbconnection']['DB_PASSWORD'],
            host=config['dbconnection']['DB_HOST'],
            port=config['dbconnection']['DB_PORT'],
            database=config['dbconnection']['DB_NAME']
        )
       
        # Check for a SSL certificate.
        ssl_cert_file = config['dbconnection']["SSL_CERT"].strip()
        if len(ssl_cert_file) > 0:
            if not os.path.isfile(ssl_cert_file):
                logging.error(f"SSL Certificate file not found, no such file named \"{ssl_cert_file}\"")
                return None
        connection_args.update({'ssl': {'ca': ssl_cert_file}})

    except KeyError as e:
        logging.error(e)
        return None

    engine = create_engine(connection_string, connect_args=connection_args, echo=True, future=True)

    # Test the connection.
    try:
        engine.connect()
        con = engine.connect()
        con.close()
        print("Connected to Azure MySQL successfully!")
        return engine
    
    except exc.OperationalError as err:
        print(err.__cause__)
        return None


def initialise_db(engine) -> None:
    # # Check that the engine exists
    if engine is None:
        return
     
    # Create an all tables database, ignoring any tables present.
    Base.metadata.create_all(engine)

    session = Session(engine)
    # If first-time setup, populate the directions table.
    statement = select(Direction)
    result = session.execute(statement)
    returned_results = []
    for r in result:
        returned_results.append(r._data[0].to_dict())
    num_directions = len(returned_results)
    if num_directions != 16:
        create_direction_table(session)
        session.commit()
    session.close()


def create_direction_table(session):
    # On initialisation, directions table should be empty.
    statement = delete(Direction).where(Direction.direction_id)
    session.execute(statement)
    session.commit()

    # Read Excel file into DataFrame
    df = pd.read_excel('WeatherSvc\MetOfficeWeather.xlsx', sheet_name='Compass')
    
    # Iterate through the DataFrame, create a new direction object, and add to the list
    x = 0
    for row in df.iterrows():
        new_direction_object = Direction( df.iloc[x][0])
        session.add(new_direction_object)
        x += 1  
    session.commit()


def get_from_db(session, table_name, id):
    statement = None
    if table_name == 'stations':
        if id:
            statement = select(Station).where(Station.station_id == id)
        else:
            statement = select(Station)
    elif table_name == 'directions':
        if id:
            statement = select(Direction).where(Direction.direction_id == id)
        else:
            statement = select(Direction)
    elif table_name == 'measurements':
        if id:
            statement = select(Measurement).where(Measurement.station_id == id)
        else:
            statement = select(Measurement)

    result = session.execute(statement)
    return result 


def get_measurements(session, measurement_id):
    if measurement_id:
        statement = select(Measurement).where(Measurement.measurement_id == measurement_id)
        return session.execute(statement)
    statement = select(Measurement)
    return session.execute(statement)


def insert_station(session,  stat_ser):
    statement = insert(Station).values(station_serial=stat_ser)
    try:
        result = session.execute(statement)
    except exc.IntegrityError as e:
        return e
    session.commit()
    return result.inserted_primary_key._data[0]


def delete_station(session, delete_id):
    statement = delete(Station).where(Station.station_id==delete_id)
    result = session.execute(statement)
    session.commit()
    return result


def setup_home(app, session):
    @app.route('/', endpoint = 'home', methods=['GET']) 
    def home():
        return make_response(jsonify("Welcome to the homepage."), 200)

    
def setup_direction_routes(app, session):
    @app.route('/directions/', endpoint = 'directionsAll', defaults={'direction_id': None}, methods=['GET'])  
    @app.route('/directions/<int:direction_id>', endpoint = 'directionsById', methods=['GET'])
    def directions(direction_id):
        directions = None
        if request.method == 'GET':
            if not direction_id:
                directions = get_from_db(session, 'directions', None)
            else:
                directions = get_from_db(session, 'directions', direction_id)        
            if not directions:
                return make_response(jsonify(logging.error("Error: This table is empty, no directions found.")), 204)
            returned_results = []
            for d in directions:
                returned_results.append(d._data[0].to_dict())
            return return_results(returned_results, direction_id, 'directions')
        return make_response(jsonify(logging.error("Error: This HTML method not supported.")), 405)


def setup_station_routes(app,session):
    @app.route('/stations/', endpoint = "stationsAll", defaults={'station_id': None}, methods=['GET', 'POST'])
    @app.route('/stations/<int:station_id>', endpoint = "stationsById", methods=['GET', 'DELETE'])
    def stations(station_id):
        stations = None    
        if request.method == 'GET':
            if not station_id:
                stations = get_from_db(session, 'stations', None)
            else:
                stations = get_from_db(session, 'stations', station_id)  
            returned_results = []
            for s in stations:
                returned_results.append(s._data[0].to_dict())
            return return_results(returned_results, station_id, 'stations')

        if request.method == 'POST':
            try:
                response_id = insert_station(session, request.json["station_serial"])
                if not isinstance(response_id, int):
                    station_serial = request.json['station_serial']
                    logging.error(response_id)
                    return make_response(jsonify(f"Error: entry with that {station_serial} already exists.  No new entry added."), 501)
                else:
                    logging.info(f"New entry added with response id {response_id}.")
                    return make_response(jsonify(response_id), 200)
            except TypeError:
                return make_response(jsonify(logging.error("Error: No JSON supplied.")), 500)
            except KeyError:
                return make_response(jsonify(logging.error("Error: Missing JSON data.")), 500)
            except Exception:
                return make_response(jsonify(logging.error("Error: Internal server error.")), 500)
        
        if request.method == 'DELETE':
            stations = delete_station(session, station_id)
            if not stations:
                return make_response(jsonify(logging.error(f"Error: id({station_id}) not found in the stations table, no station was deleted.")), 405)
            return make_response(jsonify(logging.info(f"Success: station with id({station_id}) successfully deleted.")), 200)
        
        return make_response(jsonify(logging.error(f"Error: HTML method ({request.method}) not supported.")), 405)
    

def setup_measurement_routes(app, session):
    @app.route('/measurements/', defaults= {"station_serial": None}, endpoint = "measurementsAll", methods=['GET'])
    @app.route('/measurements/<int:station_serial>', endpoint = "measurementsByStationId",  methods=['GET'])
    def measurements(station_serial):
        measurements = None
        if request.method == 'GET':
            if not station_serial:
                measurements = get_from_db(session, 'measurements', None)
            else:
                measurements = get_measurements(session, 'measurements', station_serial)
            if not measurements:
                return make_response(jsonify(logging.error("Error: This table is empty, no measurements found.")), 204)
            
            returned_results = []
            for m in measurements:
                returned_results.append(m._data[0].to_dict())
            return return_results(returned_results, station_serial, 'measurements')
        return make_response(jsonify(logging.error(f"Error: HTML method ({request.method}) not supported.")), 405)


def return_results(returned_results, id, table_name):
        if (len(returned_results) == 0) and (not id):
            return make_response(jsonify(logging.error(f"Error: This table is empty, no {table_name} found.")), 204)
        if (len(returned_results) == 0) and (id):
            return make_response(jsonify(logging.error(f"Error: No {table_name} with ID({id}) can be found.")), 204)
        return jsonify(returned_results, 201)


def setup_routes(app, engine):
    session = Session(engine)
    setup_home(app, session)
    setup_direction_routes(app, session)
    setup_station_routes(app, session)
    setup_measurement_routes(app, session)
    session.close()


def create_app(app) -> Flask:  
    engine = mysql_engine('WeatherSvc/db_connection.ini')
    initialise_db(engine)
    setup_routes(app, engine)
    return app.run(debug=True, use_reloader=False, host='0.0.0.0', port=80)


def main() -> None:
    app = create_app()
    return app.run(debug=True, use_reloader=False)



app = Flask(__name__) 
create_app(app)
