# Lightweight FaaS Platform (Internal Proof-of-Concept)

This repository contains the design and implementation of a lightweight Function-as-a-Service (FaaS) platform execution runtime. It was designed to meet the specific requirements of low latency and internal usage for AryaXAI.

## 📂 Project Structure

* **`DESIGN.md`**: The primary architectural document. It details the High-Level Architecture, Invocation Flows, and the justification for choosing a **Process-based** approach over Containers.
* **`runtime_host.py`**: The core runtime engine. It sets up an HTTP server and dynamically loads user functions into memory.
* **`my_function.py`**: A sample user function used to demonstrate the platform's capabilities.

## 🚀 Architectural Approach

The core decision for this platform was to utilize a **Process-based execution model** rather than a Container-based one.

* **Performance:** By running functions as processes, we eliminate the heavy "Cold Start" penalty associated with spinning up containers (Docker).
* **Simplicity:** The runtime uses the Python standard library (`http.server`, `importlib`) with zero external dependencies, making it extremely lightweight and easy to audit.
* **Flexibility:** The runtime dynamically imports code based on environment variables, allowing for hot-swapping of function logic.

## 🛠️ How to Run

### Prerequisites
* Python 3.x

### 1. Start the Runtime Server
The runtime requires the `USER_FUNC_PATH` environment variable to be set, pointing to the function file you wish to execute.

**On Windows (PowerShell):**
```powershell
$env:USER_FUNC_PATH = "$PWD\my_function.py"
python runtime_host.py

On Windows (CMD):

DOS

set "USER_FUNC_PATH=%cd%\my_function.py"
python runtime_host.py
You should see the message: FaaS Runtime listening on port 8080...

2. Test the function
Open a new terminal window and send a POST request with a JSON payload.

Using PowerShell:

PowerShell

Invoke-RestMethod -Uri "http://localhost:8080" -Method Post -Body '{"name": "AryaXAI Team"}' -ContentType "application/json"
Expected Output:

JSON

{"result": "Hello, AryaXAI Team! This is running on AryaXAI FaaS."}
