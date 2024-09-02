import time
import grpc
import data_stream_pb2
import data_stream_pb2_grpc
from concurrent import futures
import numpy as np
import threading
import queue

# Queue to hold the shared data for broadcasting
data_queue = queue.Queue()

class DataStreamerServicer(data_stream_pb2_grpc.DataStreamerServicer):
    def StreamData(self, request, context):
        while True:
            # Check if there's data in the queue
            if not data_queue.empty():
                # Get the next data point from the queue
                data_point = data_queue.get()
                # Yield the data point to the client
                yield data_point

def data_generator():
    while True:
        # Generate data points for both distributions
        normal_value = np.random.normal(0, 1)
        power_law_value = np.random.power(5) - 0.5  # Shift for visualization
        
        # Create a DataPoint message
        data_point = data_stream_pb2.DataPoint(
            normal_value=normal_value,
            power_law_value=power_law_value
        )
        
        # Put the data point in the queue (broadcast)
        data_queue.put(data_point)
        
        # Sleep for a bit to simulate streaming
        time.sleep(0.1)

def serve():
    # Start the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    data_stream_pb2_grpc.add_DataStreamerServicer_to_server(DataStreamerServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051")
    
    # Start the data generation thread
    data_gen_thread = threading.Thread(target=data_generator)
    data_gen_thread.daemon = True  # Daemon thread will exit when main thread exits
    data_gen_thread.start()

    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
