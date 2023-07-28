import json
import boto3
from shapely.geometry import Polygon
from shapely.geometry.base import dump_coords
import utm 


s3 = boto3.client("s3")
bucket_name = "boundary-plot"

def expand_bbox(bbox, margin):
    min_lon, min_lat, max_lon, max_lat = bbox

    # Expand the bounding box by adding/subtracting the margin
    min_lon -= margin
    min_lat -= margin
    max_lon += margin
    max_lat += margin

    return [[min_lon, min_lat], [max_lon, max_lat]]

def stretch_bbox(bbox, gsd=0.0001):
    
    stretch_amount = gsd / 2.0

    lat1, lon1 = bbox[0]
    utm_x1, utm_y1, _, _ = utm.from_latlon(lat1, lon1)

    lat2, lon2 = bbox[1]
    utm_x2, utm_y2, _, _ = utm.from_latlon(lat2, lon2)

    stretched_utm_bbox = [
        [utm_x1 - stretch_amount, utm_y1 - stretch_amount],
        [utm_x2 + stretch_amount, utm_y2 + stretch_amount]
    ]

    latlon1 = utm.to_latlon(stretched_utm_bbox[0][0], stretched_utm_bbox[0][1], zone_number=utm.from_latlon(lat1, lon1)[2], northern=lat1 >= 0)
    latlon2 = utm.to_latlon(stretched_utm_bbox[1][0], stretched_utm_bbox[1][1], zone_number=utm.from_latlon(lat2, lon2)[2], northern=lat2 >= 0)

    stretched_bbox = [list(latlon1), list(latlon2)]

    print(stretch_bbox)
    
    return stretched_bbox




def get_bbox_from_geojson(bucket_name, key_name):
    
    try:
        print("Downloading")
        d = s3.list_objects_v2(Bucket=bucket_name,Prefix=key_name)
        print(d)
        response = s3.get_object(Bucket=bucket_name, Key=key_name)
        
    except:
        return "Not Found"
        
    geojson_str = response['Body'].read().decode('utf-8')
    
    geojson_data = json.loads(geojson_str)
    
    coordinates = geojson_data['geometry']['coordinates']
    polygon = Polygon(coordinates[0])
    b = polygon.bounds
    bbox = expand_bbox(b, 0.00001)


    #bbox = [[b[0],b[1]],[b[2],b[3]]]
    print(bbox, type(bbox))
    # Stretch the bbox by 10 meters GSD
    stretched_bbox = stretch_bbox(bbox, gsd=10)

    # The new bbox after stretching in latitude and longitude format
    print(stretched_bbox)
    
    polygon = Polygon(coordinates[0])
    wkt = polygon.wkt
   
    #Get the area of the polygon feature
    area = geojson_data['properties']['area']
    
    return stretched_bbox, wkt, area
    
    


def lambda_handler(event, context):
    # TODO implement
    print("_____LATEST DEPLOYMENT _______")
    print("Received event: " + json.dumps(event, indent=2))
    
    farm_id = event["queryStringParameters"]["farmID"]
    farm_name = event["queryStringParameters"]["farmName"]
    
    geojson_key = f"{farm_id}_{farm_name}.geojson"
    print(geojson_key)
    
    try :
        
        imageoverlaycoords ,fieldboundary, area = get_bbox_from_geojson(bucket_name, geojson_key)
        
    except :
        return {
            "statusCode" : 404,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,access-control-allow-origin",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Origin": "*",
            },
            "body" : json.dumps({
                "message" : "Please check farmID/farmName"
            })
        }
    
    print(area, type(area))
    
    
    
    result = {
        "imageoverlaycoords" : imageoverlaycoords,
        "fieldboundary" : fieldboundary,
        "area" : str(area)[:4]
        }
    
    # Return the bbox as the response
    response = {
        "statusCode": 200,
        "body": json.dumps(result),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,access-control-allow-origin",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Origin": "*",
        },
    }

    return response