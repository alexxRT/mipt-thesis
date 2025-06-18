import tensorflow as tf
import json
from google.protobuf.json_format import MessageToJson
from tensorflow.core.profiler.protobuf import xplane_pb2
import os

def convert_profiler_pb_to_json(pb_file_path, output_json_path):
    if not os.path.exists(pb_file_path):
        raise FileNotFoundError(f"File not found: {pb_file_path}")

    print(f"TensorFlow version: {tf.__version__}")

    with open(pb_file_path, 'rb') as f:
        data = f.read()

    print(f"File size: {len(data)} bytes")

    xspace = xplane_pb2.XSpace()
    xspace.ParseFromString(data)
    json_output = MessageToJson(xspace, preserving_proto_field_name=True)
    json_object = json.loads(json_output)

    with open(output_json_path, "w") as dJson:
        json.dump(json_object, dJson, indent=2)

if __name__ == "__main__":
    pb_file = "output_protobuf/trace.xplane.pb"
    json_file = "output_json/trace.xplane.json"

    try:
        convert_profiler_pb_to_json(pb_file, json_file)
        print("Conversion successful!")

    except Exception as e:
        print(f"Conversion failed: {e}")