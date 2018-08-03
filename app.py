import json
import os
import random
import numpy as np
import requests
from geojson import Point, Feature
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, session, g, redirect, url_for, abort, jsonify,\
     render_template, flash
import geojson
import arrow
from geojson import MultiPoint, MultiPolygon, Polygon, FeatureCollection

from shapely import wkb


app = Flask(__name__)
app.config.from_object(os.environ['APP_CONFIG'])
db = SQLAlchemy(app)

from scheduler import job


from models import Household, Neighborhood

MAPBOX_ACCESS_KEY = app.config['MAPBOX_ACCESS_KEY']

ROUTE = [
    {"lat": 64.0027441, "long": -22.7066262, "name": "Keflavik Airport", "is_stop_location": True},
    {"lat": 64.0317168, "long": -22.1092311, "name": "Hafnarfjordur", "is_stop_location": True},
    {"lat": 63.99879, "long": -21.18802, "name": "Hveragerdi", "is_stop_location": True},
    {"lat": 63.4194089, "long": -19.0184548, "name": "Vik", "is_stop_location": True},
    {"lat": 63.5302354, "long": -18.8904333, "name": "Thakgil", "is_stop_location": True},
    {"lat": 64.2538507, "long": -15.2222918, "name": "Hofn", "is_stop_location": True},
    {"lat": 64.913435, "long": -14.01951, "is_stop_location": False},
    {"lat": 65.2622588, "long": -14.0179538, "name": "Seydisfjordur", "is_stop_location": True},
    {"lat": 65.2640083, "long": -14.4037548, "name": "Egilsstadir", "is_stop_location": True},
    {"lat": 66.0427545, "long": -17.3624953, "name": "Husavik", "is_stop_location": True},
    {"lat": 65.659786, "long": -20.723364, "is_stop_location": False},
    {"lat": 65.3958953, "long": -20.9580216, "name": "Hvammstangi", "is_stop_location": True},
    {"lat": 65.0722555, "long": -21.9704238, "is_stop_location": False},
    {"lat": 65.0189519, "long": -22.8767959, "is_stop_location": False},
    {"lat": 64.8929619, "long": -23.7260926, "name": "Olafsvik", "is_stop_location": True},
    {"lat": 64.785334, "long": -23.905765, "is_stop_location": False},
    {"lat": 64.174537, "long": -21.6480148, "name": "Mosfellsdalur", "is_stop_location": True},
    {"lat": 64.0792223, "long": -20.7535337, "name": "Minniborgir", "is_stop_location": True},
    {"lat": 64.14586, "long": -21.93955, "name": "Reykjavik", "is_stop_location": True},
]

# Mapbox driving direction API call
ROUTE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{0}.json?access_token={1}&overview=full&geometries=geojson"

def create_route_url():
    # Create a string with all the geo coordinates
    lat_longs = ";".join(["{0},{1}".format(point["long"], point["lat"]) for point in ROUTE])
    # Create a url with the geo coordinates and access token
    url = ROUTE_URL.format(lat_longs, MAPBOX_ACCESS_KEY)
    return url

def create_stop_location_detail(title, latitude, longitude, index, route_index):
    point = Point([longitude, latitude])
    properties = {
        "title": title,
        'icon': "campsite",
        'marker-color': '#3bb2d0',
        'marker-symbol': index,
        'route_index': route_index
    }
    feature = Feature(geometry = point, properties = properties)
    return feature

def create_stop_locations_details():
    stop_locations = []
    for route_index, location in enumerate(ROUTE):
        if not location["is_stop_location"]:
            continue
        stop_location = create_stop_location_detail(
            location['name'],
            location['lat'],
            location['long'],
            len(stop_locations) + 1,
            route_index
        )
        stop_locations.append(stop_location)
    return stop_locations

def get_route_data():
    # Get the route url
    route_url = create_route_url()
    # Perform a GET request to the route API
    result = requests.get(route_url)
    # Convert the return value to JSON
    data = result.json()

    geometry = data["routes"][0]["geometry"]
    route_data = Feature(geometry = geometry, properties = {})
    waypoints = data["waypoints"]
    return route_data, waypoints



@app.route('/mapbox_js')
def mapbox_js():
    route_data, waypoints = get_route_data()

    stop_locations = create_stop_locations_details()

    return render_template('mapbox_js.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        route_data=route_data,
        stop_locations = stop_locations
    )

@app.route('/mapbox_gl')
def mapbox_gl():
    route_data, waypoints = get_route_data()

    stop_locations = create_stop_locations_details()

    # For each stop location, add the waypoint index 
    # that we got from the route data
    for stop_location in stop_locations:
        waypoint_index = stop_location.properties["route_index"]
        waypoint = waypoints[waypoint_index]
        stop_location.properties["location_index"] = route_data['geometry']['coordinates'].index(waypoint["location"])

    return render_template('mapbox_gl.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        route_data = route_data,
        stop_locations = stop_locations
    )



############# Draw neighborhood manually ######################
@app.route('/')
def index():
    neighs = []
    neighborhoods = Neighborhood.query.all()
    for neigh in neighborhoods:
        if not neigh.name in neighs:
            neighs.append(neigh.name)

    households = Household.query.filter(Household.geom != None).all()
    points = []
    for hs in households:
        point = wkb.loads(str(hs.geom), hex=True)
        points.append((point.x, point.y))
    feature = Feature(geometry=MultiPoint(points), id=1)
    return render_template('neigh.html',
                           ACCESS_KEY=MAPBOX_ACCESS_KEY,
                           neighs = neighs,
                           data=geojson.dumps(feature)
                           )

@app.route('/neigh/add', methods=['POST'])
def add_neighborhood():
    data = request.json
    name = data['name']
    geom = data['geom']
    if geom:
        db.session.execute("delete from essex_neighborhood where name='%(name)s'" % data)
        for feature in geom['features']:
            coordinates = feature['geometry']['coordinates'][0]
            s = ', '.join([' '.join(map(str, cor)) for cor in coordinates])
            db.session.add(Neighborhood(feature['id'], name, 'SRID={};POLYGON(({}))'.format(4326, s)))
        db.session.commit()
        neighs, colors = getNeighborhoodFeatureCollection(name)
        return jsonify(neighs)
    return "OK"


@app.route('/neigh/delete', methods=['POST'])
def delete_neighborhood():
    data = request.json
    name = data['name']
    if name:
        db.session.execute("delete from essex_neighborhood where name='%s'" % name)
        db.session.commit()
    return "OK"


@app.route('/neigh/query', methods=['POST'])
def query_neighborhoods():
    data = request.json
    neighs, colors = getNeighborhoodFeatureCollection(data['name'])
    return jsonify(neighs)


def getNeighborhoodFeatureCollection(name):
    neighborhoods = Neighborhood.query.filter(Neighborhood.name==name).order_by(Neighborhood.id).all()
    colors = generateColors(len(neighborhoods))
    features, colorDict = [], {}
    for i, neigh in enumerate(neighborhoods):
        id = neigh.id
        polygon = wkb.loads(str(neigh.geom), hex=True)
        feature = Feature(geometry=polygon, id=id)
        feature['properties'] = {
            "fill": colors[i],
            "opacity": 0.5
        }
        features.append(feature)
        colorDict[id] = colors[i]
    return FeatureCollection(features), colorDict


def generateColors(colors_num):
    return ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(colors_num)]


############ Pattern views #################
@app.route('/pattern/neigh')
def neighPatternHome():
    neighs = []
    neighborhoods = Neighborhood.query.all()
    for neigh in neighborhoods:
        if not neigh.name in neighs:
            neighs.append(neigh.name)

    households = Household.query.filter(Household.geom != None).all()
    points = []
    for hs in households:
        point = wkb.loads(str(hs.geom), hex=True)
        points.append((point.x, point.y))
    households = Feature(geometry=MultiPoint(points), id=1)
    return render_template('neighpattern.html',
                           ACCESS_KEY=MAPBOX_ACCESS_KEY,
                           neighs = neighs,
                           households=geojson.dumps(households)
                           )

@app.route('/pattern/neigh/avg', methods=['POST'])
def patternByNeighborhoods():
    data = request.json
    name = data['name']
    if name:
        neighs, colors = getNeighborhoodFeatureCollection(name)
        result = db.session.execute("select id, readings from essex_consumption_patterns where name=:name", {'name':name})
        lines = {}
        for row in result.fetchall():
            id, readings = row
            lines[id] = [(i, reading) for i, reading in enumerate(readings)]
        series = [{'type':'line', 'color':colors[id], 'data': lines[id]} for id in lines]
        return jsonify({'featureCollections': neighs, 'series':series})
    return 'OK'


@app.route('/pattern/clustering')
def clusteringPattern():
    neighs = []
    neighborhoods = Neighborhood.query.all()
    for neigh in neighborhoods:
        if not neigh.name in neighs:
            neighs.append(neigh.name)

    households = Household.query.filter(Household.geom != None).all()
    points = []
    for hs in households:
        point = wkb.loads(str(hs.geom), hex=True)
        points.append((point.x, point.y))
    households = Feature(geometry=MultiPoint(points), id=1)
    clusters, colors = getClusteredLayers()
    series = getClusteringPatterns(colors)
    return render_template('clusteringpattern.html',
                           ACCESS_KEY=MAPBOX_ACCESS_KEY,
                           neighs = neighs,
                           households=geojson.dumps(households),
                           clusters = geojson.dumps(clusters),
                           series = geojson.dumps(series)
                           )

##########################################
def getClusteredLayers():
    rows = db.session.execute(
        "select B.clusterid, A.lon, A.lat from essex_meters A, essex_consumption_patterns_forclustering B where A.meterid=B.meterid and A.geom is not null").fetchall()
    clusters = {}
    for row in rows:
        clusterid, lon, lat = row
        points = clusters.get(clusterid, [])
        points.append((lon, lat))
        clusters[clusterid] = points

    colors = generateColors(len(clusters))
    layers = []
    for clusterid in clusters:
        layers.append({
            "id": 'cluster-' + str(clusterid),
            "type": "circle",
            "paint": {
                "circle-color": colors[clusterid],
                'circle-radius': {
                    'base': 1.75,
                    'stops': [[12, 2], [22, 180]]
                },
            },
            "source": {
                "type": "geojson",
                "data": {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "MultiPoint",
                            "coordinates": clusters.get(clusterid)
                        }
                    }]
                }
            }
        })
    return layers, colors


def getClusteringPatterns(colors):
    #neighs, colors = getNeighborhoodFeatureCollection(name)
    #https://stackoverflow.com/questions/48394404/how-to-give-different-colors-to-marker-circle-in-mapbox-gl-js?rq=1
    rows = db.session.execute("select id, readings from essex_consumption_patterns where seg_type=3").fetchall()
    if len(rows)>0:
        lines = {}
        for row in rows:
            clusterid, readings = row
            id = int(clusterid)
            lines[id] = [(i, reading) for i, reading in enumerate(readings)]
        series = [{'type':'line', 'color':colors[id], 'data': lines[id]} for id in lines]
        return series
    else:
        return []





@app.route('/job/start')
def startJob():
    job.start()
    return 'Job was started'

@app.route('/job/stop')
def stopJob():
    job.stop()
    return 'Job was stopped!'

@app.route('/job/status')
def stopStatus():
    return job.status()



@app.route('/dynamic')
def dynamic():
    return render_template('dynamic.html',
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        data={}
    )


@app.route('/savegeo')
def savegeo():
    return render_template('savegeo.html',
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        data={}
    )
