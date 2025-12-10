import os
import sys
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configuration
PORT = 8080
FUNCTION_PATH = os.environ.get('USER_FUNC_PATH')

if not FUNCTION_PATH:
    print("Error: USER_FUNC_PATH environment variable not set.")
    sys.exit(1)

# Helper: Dynamically load the user function
def load_user_function(path):
    try:
        # Extract directory and filename
        module_dir, module_file = os.path.split(path)
        module_name = os.path.splitext(module_file)[0]
        
        # Add module dir to sys.path so imports within the user function work
        sys.path.append(module_dir)
        
        # Dynamic import magic
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check if the 'handle' function exists
            if hasattr(module, 'handle'):
                return getattr(module, 'handle')
            else:
                raise ImportError("Function 'handle' not found in module.")
        else:
            raise ImportError(f"Could not load module from {path}")
            
    except Exception as e:
        print(f"Failed to load function: {e}")
        sys.exit(1)

# Load the function once at startup (Cold Start logic)
print(f"Loading function from {FUNCTION_PATH}...")
USER_FUNCTION = load_user_function(FUNCTION_PATH)
print("Function loaded successfully.")

class FaaSRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Read Content-Length to get body size
            content_length = int(self.headers.get('Content-Length', 0))
            
            # 2. Read the body
            post_data = self.rfile.read(content_length)
            
            # 3. Parse JSON
            if post_data:
                request_payload = json.loads(post_data.decode('utf-8'))
            else:
                request_payload = {}

            # 4. Invoke the user's function
            result = USER_FUNCTION(request_payload)
            
            # 5. Send Response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response_data = json.dumps({"result": result})
            self.wfile.write(response_data.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            error_msg = json.dumps({"error": str(e)})
            self.wfile.write(error_msg.encode('utf-8'))

    def log_message(self, format, *args):
        # Override to keep console output clean or redirect logs
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))

if __name__ == '__main__':
    server = HTTPServer(('localhost', PORT), FaaSRequestHandler)
    print(f"FaaS Runtime listening on port {PORT}...")
    server.serve_forever()
