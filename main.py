from datetime import datetime as dt
from datetime import date
from datetime import datetime
import json
import urllib.request
#import sqlalchemy as db
import folium
import folium.plugins.feature_group_sub_group as subGroup
from folium import plugins
import pandas
from flask import Flask, render_template_string, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Interval, Time
from sqlalchemy.orm import Mapped, mapped_column
#from dateutil import rrule
#from dateutil import relativedelta

def delete_databases():
    with app.app_context():
        db.drop_all()
def make_databases():
    with app.app_context():
        db.create_all()
db = SQLAlchemy()
# create the app
app = Flask(__name__,static_folder="assets")
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///main.db"
# initialize the app with the extension
db.init_app(app)
class genParking(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[int] = mapped_column(String, nullable=False)
    start: Mapped[Time] = mapped_column(Time, nullable=False)
    end: Mapped[Time] = mapped_column(Time, nullable=False)
#genParkingTimes=[[0,datetime.time()]]
def retrieve_closed_dates():
    print("test")
def fillGenParking():
    genParking = [(7,16) for i in range(7)]
    genParking[5] = (0,0)
    genParking[6] = (0,0)
    return genParking
#Returns true if it's a visitor exception holiday
def calcFreeParking():
    genParking = fillGenParking()
    weekDay = date.today().weekday()
    return not genParking[weekDay][0]<=datetime.now().hour<=genParking[weekDay][1]
def checkHolidays():
    today = date.today()
    if(today==date(today.year, 1, 1)):
        return True
    elif(today==date(today.year,1,today.day) and today.weekday()==0 and 15<=today.day<=21):
        return True
    elif(today==date(today.year,5,today.day) and today.weekday()==0 and 25<=today.day<=31):
        return True
    elif(today==date(today.year, 6, 19)):
        return True
    elif(today==date(today.year, 7, 4)):
        return True
    elif(today==date(today.year,11,today.day) and today.weekday()==3 and 22<=today.day<=28):
        return True
    elif(today==date(today.year,11,today.day) and today.weekday()==4 and 23<=today.day<=29):
        return True
    elif(today==date(today.year,12,today.day) and today.day>=25):
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
    #print(openFoodLocations['Commons Retriever Market'][1].strftime('%H:%M'))
    return openFoodLocations

def add_feature_groups(folium_map, permits):
    for permit_type in permits:
        folium_map.add_child(permits[permit_type][1])

# Returns a list of lists of tuples containing coordinates
PARKING_COORDINATES_CSV = "coords.csv"
LOT_COORDINATES_CSV = "lot_coords.csv"
def parse_street_parking_csv(folium_map, permits, filename):
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
                color, fg = permits[previous_fg_permit]
                print(coordinates_list)
                p_line = folium.PolyLine(coordinates_list,
                                         color=color,
                                         weight=5,
                                         opacity=0.8)
                # Add the line to the feature group,
                # and add the feature group (the toggle layer) to the map.
                p_line.add_to(fg)
                coordinates_list = []
            coordinates_list.append(coordinates)
            previous_section = section_name
            previous_fg_permit = permit_type

# Probably overcomplicated, and could be made into a single function
# with the one above it.
def parse_street_lot_csv(folium_map, permits, filename):
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
                color, fg = permits[previous_fg_permit]
                if previous_fg_permit != permit_type:
                    for marker in marker_list:
                        marker.add_to(fg)
                    marker_list = []
                else:
                    marker = folium.Marker(location=coordinates, icon=folium.map.Icon(color=color))
                    marker_list.append(marker)

            previous_fg_permit = permit_type



@app.route("/")
def display_index():
    return render_template("index.html")

@app.route("/map")
def umbc_map():
    parking_fg = folium.FeatureGroup(name="Parking")
    permits = {
        "commuter"      : ("red",       subGroup.FeatureGroupSubGroup(parking_fg,name="Commuter Parking")),
        "residential"   : ("yellow",    subGroup.FeatureGroupSubGroup(parking_fg,name="Residential Parking")),
        "faculty"       : ("purple",    subGroup.FeatureGroupSubGroup(parking_fg,name="Faculty Parking")),
        "walker"        : ("green",     subGroup.FeatureGroupSubGroup(parking_fg,name="Walker Resident Parking")),
        "gated"         : ("darkpurple",subGroup.FeatureGroupSubGroup(parking_fg,name="Gated Faculty Parking")),
        "visitor"       : ("blue",subGroup.FeatureGroupSubGroup(parking_fg,name="Visitor Faculty Parking")),
    }
    #Applies to all lots A,B,C,D and visitor parking, can park in any of the mentioned lots
    freeParking = calcFreeParking()
    #Applies only to visitor parking, can park in visitor free parking
    visitorFreeParking = freeParking or checkHolidays()
    print(freeParking)
    min_longitude, max_longitude = -76.72840172303653, -76.705468
    min_latitude, max_latitude = 39.24946769219659, 39.26132540444559
    openFoodLocations = foodTimes()
    print(openFoodLocations)
    m = folium.Map(
        location=[39.2554, -76.7107],
        zoom_start=17,
        min_zoom=17,
        zoom_control=False,
        control_scale=False,
        max_bounds=True,
        min_lat=min_latitude,
        max_lat=max_latitude,
        min_lon=min_longitude,
        max_lon=max_latitude,
    )

    # Create the dining feature group
    dining_fg = folium.FeatureGroup(name='Dining Options')

    if openFoodLocations["TRUE GRIT'S"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25579239848943, -76.70774746301952],
            popup=folium.Popup("True Grit's Dining Hall"+" "+openFoodLocations["TRUE GRIT'S"][2], max_width="100%")))
    if openFoodLocations["Wild Greens"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25510631849656, -76.71111325383241],
            popup="Wild Greens"+" "+openFoodLocations["Wild Greens"][2]))
    if openFoodLocations["Halal Shack"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25518885701059, -76.71137381365875],
            popup="Halal Shack"+" "+openFoodLocations["Halal Shack"][2]))
    if openFoodLocations["Dunkin"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25456046005272, -76.71106212699955],
            popup="Dunkin'"+" "+openFoodLocations["Dunkin"][2]))
    if openFoodLocations["Chick-fil-A"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25414481349409, -76.71291550055203],
            popup="Chick-fil-A"+" "+openFoodLocations["Chick-fil-A"][2]))
    if openFoodLocations["2.Mato"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25512648103092, -76.71121394829719],
            popup="2.Mato"+" "+openFoodLocations["2.Mato"][2]))
    if openFoodLocations["Commons Retriever Market"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25512648103092, -76.71121394829719],
            popup="Commons Retriever Market"+" "+openFoodLocations["Commons Retriever Market"][2]))
    if openFoodLocations["Copperhead Jacks"][0]:    
        dining_fg.add_child(folium.Marker(
            location=[39.255148288803476, -76.71127094523622],
            popup="Copperhead Jacks"+" "+openFoodLocations["Copperhead Jacks"][2]))
    if openFoodLocations["Hissho"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25519189438983, -76.71127028124181],
            popup="Hissho"+" "+openFoodLocations["Hissho"][2]))
    if openFoodLocations["rbc"][0]:    
        dining_fg.add_child(folium.Marker(
            location=[39.25518930816724, -76.71124479370278],
            popup="rbc"+" "+openFoodLocations["rbc"][2]))
    if openFoodLocations["The Skylight Room"][0]:    
        dining_fg.add_child(folium.Marker(
            location=[339.255008462116535, -76.71068141955072],
            popup="The Skylight Room"+" "+openFoodLocations["The Skylight Room"][2]))
    if openFoodLocations["Sorrentos"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25519657741852, -76.71135476426421],
            popup="Sorrentos"+" "+openFoodLocations["Sorrentos"][2]))
    if openFoodLocations["Student Choice"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25512232716872, -76.71133397714527],
            popup="Student Choice"+" "+openFoodLocations["Student Choice"][2]))
    if openFoodLocations["Einstein Brother's Bagels"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25640491623738, -76.71162495241681],
            popup="Einstein Brother's Bagels"+" "+openFoodLocations["Einstein Brother's Bagels"][2]))
    if openFoodLocations["Starbucks"][0]:
        dining_fg.add_child(folium.Marker(
            location=[39.25427471682431, -76.71323086681052],
            popup="Starbucks"+" "+openFoodLocations["Starbucks"][2]))
    if openFoodLocations["The Coffee Shop"][0]:    
        dining_fg.add_child(folium.Marker(
            location=[39.25294158464396, -76.71348604175182],
            popup="The Coffee Shop"+" "+openFoodLocations["The Coffee Shop"][2]))
    if openFoodLocations["True Grit's Retriever Market"][0]:    
        dining_fg.add_child(folium.Marker(
            location=[39.25568457647287, -76.70773784764805],
            popup="True Grit's Retriever Market"+" "+openFoodLocations["True Grit's Retriever Market"][2]))
        
        m.add_child(dining_fg)

    folium.CircleMarker([max_latitude, min_longitude], tooltip="Upper Left Corner").add_to(m)
    folium.CircleMarker([min_latitude, min_longitude], tooltip="Lower Left Corner").add_to(m)
    folium.CircleMarker([min_latitude, max_longitude], tooltip="Lower Right Corner").add_to(m)
    folium.CircleMarker([max_latitude, max_longitude], tooltip="Upper Right Corner").add_to(m)
    parse_street_parking_csv(m, permits, PARKING_COORDINATES_CSV)
    parse_street_lot_csv(m, permits, LOT_COORDINATES_CSV)
    m.add_child(parking_fg)
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
    print(genParking)
    app.run()
    #delete_databases()
    #make_databases()
    #with app.app_context():
    #    print(genParking.query.all())
    #print(str(dt.date.today()))
