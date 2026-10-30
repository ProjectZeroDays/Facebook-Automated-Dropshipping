from flask import Response
import time

def notify_stream():
    def event_stream():
        while True:
            time.sleep(2)
            yield "data: {\"status\":\"live\",\"ts\":\"now\"}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')
