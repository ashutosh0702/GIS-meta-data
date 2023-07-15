import json
import boto3
from shapely.geometry import Polygon
from shapely.geometry.base import dump_coords
import rasterio


s3 = boto3.client("s3")
bucket_name = "boundary-plot"
bucket_raster = "sentinel-2-cogs-rnil"

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
    bbox = [[b[0],b[1]],[b[2],b[3]]]
    print(bbox, type(bbox))
    
    
    
    
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
    
    farmID = event["queryStringParameters"]["farmID"]
    farmName = event["queryStringParameters"]["farmName"]
    
    geojson_key = f"{farmID}_{farmName}.geojson"
    
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

    try :
        objects = s3.list_objects_v2(Bucket=bucket_raster, Prefix=f"{farmID}_{farmName}")['Contents']
        print(type(objects), objects)
        res = next(iter(objects))
        
        print(res)

        s3.download_file(bucket_name,res,f"/tmp/{farmID}_raster.tif")

        with rasterio.open(f"/tmp/{farmID}_raster.tif") as src:

            bbox_ras = src.get_bbox()

        print(bbox_ras,imageoverlaycoords)
    except:
        print("Error downloading")
    
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