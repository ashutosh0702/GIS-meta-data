import json
import boto3
from shapely.geometry import Polygon
from shapely.geometry.base import dump_coords


s3 = boto3.client("s3")
bucket_name = "boundary-plot"

def expand_bbox(bbox, margin):
    min_lon, min_lat, max_lon, max_lat = bbox

    # Expand the bounding box by adding/subtracting the margin
    min_lon -= margin
    min_lat -= margin
    max_lon += margin
    max_lat += margin

    return [min_lon, min_lat, max_lon, max_lat]

def get_bbox_from_geojson(bucket_name, key_name):
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key_name)
        
    except:
        return "Not Found"
        
    geojson_str = response['Body'].read().decode('utf-8')
    
    geojson_data = json.loads(geojson_str)
    
    coordinates = geojson_data['geometry']['coordinates']
    polygon = Polygon(coordinates[0])
    b = polygon.bounds
    bbox = expand_bbox(b, 10)


    #bbox = [[b[0],b[1]],[b[2],b[3]]]
    print(bbox, type(bbox))
    
    '''
    # Flatten the list of coordinates
    flattened_coords = [item for sublist in coordinates for item in sublist]
    # Extract min and max values for each dimension
    min_x, min_y = min(coord[0] for coord in flattened_coords), min(coord[1] for coord in flattened_coords)
    max_x, max_y = max(coord[0] for coord in flattened_coords), max(coord[1] for coord in flattened_coords)
    # Swap min and max values for y (latitude) to align with north-oriented map
    #min_y, max_y = max_y, min_y
    # Return lower left and upper right coordinates
    bbox = [[min_x, min_y], [max_x, max_y]]
    '''
    
    
    print(bbox)
    polygon = Polygon(coordinates[0])
    wkt = polygon.wkt
   
    #Get the area of the polygon feature
    area = geojson_data['properties']['area']
    
    return bbox, wkt, area
    
    


def lambda_handler(event, context):
    # TODO implement
    print("_____LATEST DEPLOYMENT _______")
    print("Received event: " + json.dumps(event, indent=2))
    
    farm_id = event["queryStringParameters"]["farmID"]
    farm_name = event["queryStringParameters"]["farmName"]
    
    geojson_key = f"{farm_id}_{farm_name}.geojson"
    
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