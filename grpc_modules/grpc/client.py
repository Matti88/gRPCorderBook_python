import grpc
import data_stream_pb2
import data_stream_pb2_grpc

def run():
    # Connect to the gRPC server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = data_stream_pb2_grpc.DataStreamerStub(channel)
        
        # Start streaming data
        for data_point in stub.StreamData(data_stream_pb2.Empty()):
            print(f"Received: Normal={data_point.normal_value}, Power-Law={data_point.power_law_value}")

if __name__ == '__main__':
    run()
