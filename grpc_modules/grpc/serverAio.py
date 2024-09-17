import asyncio
import grpc
import data_stream_pb2
import data_stream_pb2_grpc
import numpy as np
from concurrent import futures



class DataStreamerServicer(data_stream_pb2_grpc.DataStreamerServicer):
    def __init__(self):
        # List to store client response streams (tasks)
        self.clients = []
    
    async def StreamData(self, request, context):
        # Add the client stream to the list
        queue = asyncio.Queue()
        self.clients.append(queue)

        try:
            while True:
                # Await the next data point for this client
                data_point = await queue.get()
                yield data_point
        except asyncio.CancelledError:
            # If the client disconnects or cancels, remove the stream
            self.clients.remove(queue)
            raise
    
    async def broadcast_data(self):
        while True:
            # Generate data points for both distributions
            normal_value = np.random.normal(0, 1)
            power_law_value = np.random.power(5) - 0.5  # Shift for visualization
            
            # Create a DataPoint message
            data_point = data_stream_pb2.DataPoint(
                normal_value=normal_value,
                power_law_value=power_law_value
            )
            
            # Broadcast the data point to all connected clients
            for client in self.clients:
                await client.put(data_point)
            
            # Sleep for a bit to simulate streaming
            await asyncio.sleep(0.1)

async def serve():
    # Create the gRPC server
    server = grpc.aio.server()
    data_streamer = DataStreamerServicer()
    data_stream_pb2_grpc.add_DataStreamerServicer_to_server(data_streamer, server)
    
    # Bind the server to port 50051
    server.add_insecure_port('[::]:50051')
    
    # Start the server
    await server.start()
    print("Server started on port 50051")
    
    # Start broadcasting data
    await data_streamer.broadcast_data()

    # Wait for termination
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())
