import json
import boto3
from shapely.geometry import Polygon
from shapely.geometry.base import dump_coords
import utm 


s3 = boto3.client("s3")
bucket_name = "boundary-plot"


def get_bbox_from_geojson(bucket_name, key_name):
    print(f"KEY : {key_name}")
    try:
        print("Downloading")
        d = s3.list_objects_v2(Bucket=bucket_name,Prefix=key_name)
        print(d)
        print("Getting Response")
        response = s3.get_object(Bucket=bucket_name, Key=key_name)
        
    except Exception as e:
        print(e)
        return "Not Found"
    
       
    geojson_str = response['Body'].read().decode('utf-8')
    
    print(geojson_str)
    
    geojson_data = json.loads(geojson_str)
    
    print(geojson_data)
    
    coordinates = geojson_data['geometry']['coordinates']
    polygon = Polygon(coordinates[0])
    b = polygon.bounds
    min_lon, min_lat, max_lon, max_lat = b
    
    bbox = [[min_lon, min_lat], [max_lon, max_lat]]
    
    polygon = Polygon(coordinates[0])
    wkt = polygon.wkt
   
    #Get the area of the polygon feature
    area = geojson_data['properties']['area']
    print(bbox,wkt,area)
    #return stretched_bbox, wkt, area
    return bbox , wkt , area
    


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