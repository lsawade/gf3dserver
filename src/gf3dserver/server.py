# import main Flask class and request object
from flask import Flask, request, send_file, redirect
from time import sleep
import os
from glob import glob
from pathlib import Path
from gf3d.seismograms import GFManager
from gf3d.logger import logger
import traceback


def create_app():

    # create the Flask app
    app = Flask(__name__)

    # --------------------------------------------------------
    dbpaths = {
        "example-db": "./mini-db",
        "princeton-traverse": "/scratch/gpfs/lsawade/DBSUMMIT",
        "princeton": "/home/lsawade/traverse.scratch/DBSUMMIT",
        "glad-m25": "/home/lsawade/della.tromp/GFDB/128_single"
    }
    # --------------------------------------------------------

    @app.route("/")
    def hello():
        return redirect("https://lsawade.github.io/GF3D/parts/gf-extraction/index.html")

    @app.route('/get-station-availability', methods=["GET"])
    def query_station_availability():

        print(request.method)

        allgood = True

        # Database Name
        db = request.args.get('db')
        if db is None:
            allgood = False
            return '400 - request missing "db=<database-name>" '

        if db not in dbpaths:
            return "400 -- database name not found."

        # Get station files
        station_files = glob(os.path.join(dbpaths[db], '*', '*', '*.h5'))

        # Check if stations are available
        if len(station_files) < 1:
            return "400 -- no station files found."

        # Get strings
        networks, stations = [], []

        # Sort stations
        for _file in station_files:
            net, sta, _ = os.path.basename(_file).split('.')
            networks.append(net)
            stations.append(sta)

        print(networks)
        print(stations)
        return ','.join([f'{net}.{sta}' for net, sta in zip(networks, stations)])

    @app.route('/get-db-info', methods=["GET"])
    def query_db_info():

        allgood = True

        # Database Name
        db = request.args.get('db')
        if db is None:
            allgood = False
            return '400 - request missing "db=<database-name>" '

        if db not in dbpaths:
            return "400 -- database name not found."

        # Get station files
        station_files = glob(os.path.join(dbpaths[db], '*', '*', '*.h5'))

        # Check if stations are available
        if len(station_files) < 1:
            return "400 -- no station files found."

        # Get single station's header
        station0 = station_files[0]

        # Load header
        gfm = GFManager([station0])
        header = gfm.load_scalar_header_parameters()

        print(header)

        return str(header)

    @app.route('/get-subset', methods=["GET"])
    def query_subset():

        print(request.method)

        allgood = True

        # Database Name
        db = request.args.get('db')
        if db is None:
            return '400 - request missing "db=<database-name>" '
            allgood = False

        # Latitude
        latitude = request.args.get('latitude')
        if latitude is None:
            allgood = False
            return '400 - request missing "latitude=<latitude>" '

        # Longitude
        longitude = request.args.get('longitude')
        if longitude is None:
            allgood = False
            return '400 - request missing "longitude=<longitude>" '

        # Depth
        depth = request.args.get('depth')
        if depth is None:
            allgood = False
            return '400 - request missing "depth=<depth>"'

        # Radius
        radius = request.args.get('radius')
        if radius is None:
            allgood = False
            return '400 - request missing "radius=<radius>"'

        # NGLL
        NGLL = request.args.get('NGLL')
        if NGLL is None:
            allgood = False
            return '400 - request missing "NGLL=<NGLL>"'

        # Duration
        duration = request.args.get('duration')
        if duration is not None:
            duration = float(duration)

        # Whether Fortran
        fortran = request.args.get('fortran')
        if fortran is not None:
            fortran = bool(fortran)
        else:
            fortran = False

        # Getting custom stations
        netsta = request.args.get('netsta')
        if netsta is not None:
            print(netsta)

        logger.info(f'Latitude:   {latitude}')
        logger.info(f'Longitude:  {longitude}')
        logger.info(f'Depth:      {depth}')
        logger.info(f'Radius:     {radius}')
        logger.info(f'NGLL:       {NGLL}')
        logger.info(f'Duration:   {duration}')
        logger.info(f'Fortran:    {fortran}')

        # Get station files
        station_files = glob(os.path.join(dbpaths[db], '*', '*', '*.h5'))

        # Get subset
        try:

            # Check location
            cwd = os.getcwd()
            outfile = os.path.join(cwd, 'temp.h5')

            gfm = GFManager(station_files)
            gfm.load_header_variables()

            logger.info("Writing Subset")
            gfm.write_subset_directIO(
                outfile,
                float(latitude), float(longitude), float(depth), float(radius),
                NGLL=int(NGLL), fortran=fortran)
            # gfm.get_elements(float(latitude), float(longitude), float(
            #     depth), dist_in_km=float(radius), NGLL=int(NGLL))
            # gfm.write_subset(outfile, duration=duration, fortran=fortran)

        except Exception as e:
            string = "400 -- An error was encountered when creating the subset.\n"
            string += "The exception is printed below: \n\n"
            string += f"{e} \n\n"
            string += f"{traceback.format_exc().__str__()}\n\n"
            return string

        if allgood is True:
            string = '''<h1> Values from query</h1>'''
            string += '<body>'
            string += f'Latitude: {float(latitude):10.4f}<br>'
            string += f'Longitude:{float(longitude):10.4f}<br>'
            string += f'Depth:    {float(depth):10.4f}<br>'
            string += f'Radius:   {float(radius):10.4f}<br>'
            string += '</body>'

            return send_file(outfile, as_attachment=True)
        else:
            return '400'

    return app


if __name__ == '__main__':
    app = create_app()

    # # run app in debug mode on port 5000
    app.run(debug=True, port=5000, threaded=False)
