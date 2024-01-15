from datetime import datetime as dt
from datetime import date
from datetime import datetime
from datetime import time
import json
import urllib.request
import folium
import folium.plugins.feature_group_sub_group as subGroup
from flask import Flask, render_template_string, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()
# create the app
app = Flask(__name__,static_folder="assets")
class genParking(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[int] = mapped_column(String, nullable=False)
    start: Mapped[Time] = mapped_column(Time, nullable=False)
    end: Mapped[Time] = mapped_column(Time, nullable=False)
#genParkingTimes=[[0,datetime.time()]]

def fillGenParking():
    genParking = [(7,16) for i in range(7)]
    genParking[5] = (0,0)
    genParking[6] = (0,0)
    return genParking

#Returns true if it's a visitor exception holiday
def calcFreeParking(day,time):
    genParking = fillGenParking()
    weekDay = day.weekday()
    return not genParking[weekDay][0]<=time.hour<=genParking[weekDay][1]

JAN, FEB, MAR, APR, MAY, JUN = 1, 2, 3, 4, 5, 6
JUL, AUG, SEP, OCT, NOV, DEC = 7, 8, 9, 10, 11, 12
def checkHolidays(today):
    if(today==date(today.year, JAN, 1)):
        return True
    elif(today==date(today.year, JAN,today.day) and today.weekday()==0 and 15<=today.day<=21):
        return True
    elif(today==date(today.year, MAY,today.day) and today.weekday()==0 and 25<=today.day<=31):
        return True
    elif(today==date(today.year, JUN, 19)):
        return True
    elif(today==date(today.year, JUL, 4)):
        return True
    elif(today==date(today.year, NOV,today.day) and today.weekday()==3 and 22<=today.day<=28):
        return True
    elif(today==date(today.year, NOV,today.day) and today.weekday()==4 and 23<=today.day<=29):
        return True
    elif(today==date(today.year, DEC,today.day) and today.day>=25):
        return True
    else:
        return False
    
def foodTimes():
    foodTimeJson = urllib.request.urlopen("https://api.dineoncampus.com/v1/locations/status?site_id=5751fd3690975b60e04893e2&platform=0")
    openFoodLocations = {}
    for location in json.load(foodTimeJson)['locations']:
        if location['status']['message']=='Closed.':
            openFoodLocations[location['name']] = (location['open'],"00:00","none")
        else:
            openFoodLocations[location['name']] = (location['open'],"00:00", location['status']['message'])
    return openFoodLocations

def add_feature_groups(folium_map, permits):
    for permit_type in permits:
        for group in permits[permit_type][1]:
            folium_map.add_child(group)

# Returns a list of lists of tuples containing coordinates
PARKING_COORDINATES_CSV = "coords.csv"
LOT_COORDINATES_CSV = "lot_coords.csv"
DINING_COORDINATES_CSV = "dining_coords.csv"
def parse_street_parking_csv(permits, filename):
    with open(filename) as csv_file:
        line_count = 0
        coordinates_list = []

        previous_section = ""
        previous_fg_permit = ""
        for raw_line in csv_file:
            # Skip the first line
            if line_count == 0:
                line_count += 1
                continue
            line_count += 1
            line = raw_line.strip()
            fields = line.split(",")
            permit_type, section_name = fields[0], fields[1]
            longitude, latitude = float(fields[2]), float(fields[3])

            coordinates = (longitude, latitude)
            if previous_section != section_name and previous_section != "":
                color, fgs = permits[previous_fg_permit]
                # Add the line to the feature group,
                # and add the feature group (the toggle layer) to the map.
                for fg in fgs:
                    fg.add_child(folium.PolyLine(coordinates_list,
                                    color=color,
                                    weight=5,
                                    opacity=0.8))
                coordinates_list = []
            coordinates_list.append(coordinates)
            previous_section = section_name
            previous_fg_permit = permit_type

def parse_street_lot_csv(permits, filename):
    with open(filename) as csv_file:
        line_count = 0
        marker_list = []

        previous_fg_permit = ""
        for raw_line in csv_file:
            # Skip the first line
            if line_count == 0:
                line_count += 1
                continue
            line = raw_line.strip()
            fields = line.split(",")
            permit_type, _ = fields[0], fields[1]
            longitude, latitude = float(fields[2]), float(fields[3])

            coordinates = (longitude, latitude)

            if previous_fg_permit != "":
                color, fgs = permits[previous_fg_permit]
                if previous_fg_permit != permit_type:
                    for marker in marker_list:
                        for fg in fgs:
                            fg.add_child(folium.Marker(location=marker, icon=folium.map.Icon(color=color,icon='')))
                    marker_list = []
            marker_list.append(coordinates)
            previous_fg_permit = permit_type
        color, fgs = permits["visitor"]
        for marker in marker_list:
            for fg in fgs:
                fg.add_child(folium.Marker(location=marker, icon=folium.map.Icon(color=color,icon='')))

def parse_dining_csv(openFoodLocations, filename):
    with open(filename) as csv_file:
        line_count = 0

        for raw_line in csv_file:
            # Skip the first line
            if line_count == 0:
                line_count += 1
                continue
            line = raw_line.strip()
            fields = line.split(",")
            api_name, loc_name = str(fields[0]), str(fields[1])
            longitude, latitude = float(fields[2]), float(fields[3])

            # Add the location to the dining feature group if it is currently open
            if openFoodLocations[api_name][0]:
                dining_fg.add_child(folium.Marker(
                    location=[longitude, latitude],
                    popup=folium.Popup(loc_name+" "+openFoodLocations[api_name][2],min_width=20, max_width=100)))

# Create the feature groups
dining_fg = folium.FeatureGroup(name='Dining Options')
visitor_fg = folium.FeatureGroup(name="No Permit(Visitor)", show=False)
commuter_fg = folium.FeatureGroup(name="Commuter Permit", show=False)
residential_fg = folium.FeatureGroup(name="Residential Permit", show=False)
faculty_fg = folium.FeatureGroup(name="Faculty Permit", show=False)
walker_fg = folium.FeatureGroup(name="Walker Permit", show=False)
parking_fg = folium.FeatureGroup(name="Display All Parking", show=False)

def generateAllSubGroups():
    return [subGroup.FeatureGroupSubGroup(visitor_fg, control=False), 
            subGroup.FeatureGroupSubGroup(commuter_fg, control=False),
            subGroup.FeatureGroupSubGroup(residential_fg, control=False),
            subGroup.FeatureGroupSubGroup(faculty_fg, control=False),
            subGroup.FeatureGroupSubGroup(walker_fg, control=False),
            subGroup.FeatureGroupSubGroup(parking_fg, control=False)]

@app.route("/")
def display_index():
    return render_template("index.html")

@app.route("/map")
def umbc_map():
    today = date.today()
    now = datetime.now()
    #Date and Time examples
    #today = date(2023, 9, 25)
    #now = time(12,0)
    #today = date(2024,3,18)
    #now = time(13,0)
    #Applies to all lots A,B,C,D and visitor parking, can park in any of the mentioned lots
    freeParking = calcFreeParking(today,now)
    #Applies only to visitor parking, can park in visitor free parking
    visitorFreeParking = freeParking or checkHolidays(today)
    if(freeParking):
        permits = {
            "commuter": ("red", generateAllSubGroups()),
            "residential": ("lightgreen",generateAllSubGroups()),
            "faculty": ("purple", generateAllSubGroups()),
            "walker": ("green", generateAllSubGroups()),
            "gated": ("darkpurple", [subGroup.FeatureGroupSubGroup(faculty_fg, control=False),
                                   subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "visitor": ("blue", generateAllSubGroups()),
        }
    elif(visitorFreeParking):
        permits = {
            "commuter": ("red", [subGroup.FeatureGroupSubGroup(commuter_fg, control=False),
                                 subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "residential": ("lightgreen", [subGroup.FeatureGroupSubGroup(residential_fg, control=False),
                                       subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "faculty": ("purple", [subGroup.FeatureGroupSubGroup(faculty_fg, control=False),
                                   subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "walker": ("green", [subGroup.FeatureGroupSubGroup(walker_fg, control=False),
                                   subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "gated": ("darkpurple", [subGroup.FeatureGroupSubGroup(faculty_fg, control=False),
                                   subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "visitor": ("blue", generateAllSubGroups()),
        }
    else:
        permits = {
            "commuter": ("red", [subGroup.FeatureGroupSubGroup(commuter_fg, control=False),
                                 subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "residential": ("lightgreen", [subGroup.FeatureGroupSubGroup(residential_fg, control=False),
                                           subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "faculty": ("purple", [subGroup.FeatureGroupSubGroup(faculty_fg, control=False),
                                   subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "walker": ("green", [subGroup.FeatureGroupSubGroup(walker_fg, control=False),
                                 subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "gated": ("darkpurple", [subGroup.FeatureGroupSubGroup(faculty_fg, control=False),
                                   subGroup.FeatureGroupSubGroup(parking_fg, control=False)]),
            "visitor": ("blue", [subGroup.FeatureGroupSubGroup(visitor_fg, control=False),
                                 subGroup.FeatureGroupSubGroup(parking_fg, control=False)])
        }
    min_longitude, max_longitude = -76.72840172303653, -76.705468
    min_latitude, max_latitude = 39.24946769219659, 39.26132540444559
    openFoodLocations = foodTimes()
    m = folium.Map(
        location=[39.2554, -76.7107],
        zoom_start=16,
        min_zoom=16,
        zoom_control=False,
        control_scale=False,
        max_bounds=True,
        min_lat=min_latitude,
        max_lat=max_latitude,
        min_lon=min_longitude,
        max_lon=max_latitude,
    )
 
    folium.CircleMarker([max_latitude, min_longitude], tooltip="Upper Left Corner").add_to(m)
    folium.CircleMarker([min_latitude, min_longitude], tooltip="Lower Left Corner").add_to(m)
    folium.CircleMarker([min_latitude, max_longitude], tooltip="Lower Right Corner").add_to(m)
    folium.CircleMarker([max_latitude, max_longitude], tooltip="Upper Right Corner").add_to(m)
    
    m.add_child(dining_fg)
    m.add_child(visitor_fg)
    m.add_child(residential_fg)
    m.add_child(commuter_fg)
    m.add_child(faculty_fg)
    m.add_child(walker_fg)
    m.add_child(parking_fg)
    parse_street_parking_csv(permits, PARKING_COORDINATES_CSV)
    parse_street_lot_csv(permits, LOT_COORDINATES_CSV)
    parse_dining_csv(openFoodLocations, DINING_COORDINATES_CSV)
    add_feature_groups(m, permits)
    m.add_child(folium.LayerControl(collapsed=False))
    return m.get_root().render()

def iframe():
    """Embed a map as an iframe on a page."""
    m = umbc_map()

    # set the iframe width and height
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                    <h1>Using an iframe</h1>
                    {{ iframe|safe }}
                </body>
            </html>
        """,
        iframe=iframe,
    )

if __name__ == '__main__':
    app.run()
