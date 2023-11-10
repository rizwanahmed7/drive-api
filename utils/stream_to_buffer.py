from io import BytesIO

def stream_to_buffer(stream, all_streams_to_error_catch):
    chunks = []

    for current_stream in all_streams_to_error_catch:
        current_stream.on("error", lambda e: print("Stream To Buffer Error", e))

    for chunk in stream:
        chunks.append(chunk)

    buffer_data = b"".join(chunks)
    return BytesIO(buffer_data)