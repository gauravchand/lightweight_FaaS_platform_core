# Design Document: AryaXAI Internal FaaS Platform

## 1. High-Level Architecture

The platform follows a classic master-worker architecture designed for low latency and high throughput.

**Components:**

* **API Gateway:** The entry point for all external requests. It handles authentication, request validation, and routes the invocation to the Orchestrator.
* **Orchestrator (The Brain):** Responsible for scheduling. It checks the health of the Worker Pool, decides where to schedule a function execution, and manages the lifecycle of the execution environments (scaling up/down).
* **Worker Pool (The Muscle):** A collection of nodes (servers) where the actual code executes. Each worker runs a daemon that listens for instructions from the Orchestrator.
* **Execution Runtime (The Wrapper):** The specific environment (implemented in `runtime_host.py`) that loads the user code and exposes it via HTTP.

**Architecture Diagram Description:**
[Client] -> [API Gateway] -> [Orchestrator] -> [Worker Node]
                                                     |
                                            [Execution Runtime] -> [User Function]

## 2. Invocation Flow

### A. Cold Start (High Latency)
Occurs when no active runtime exists for the requested function.

1.  **Request:** API Gateway receives a request and forwards it to the Orchestrator.
2.  **Lookup:** Orchestrator checks for an available "warm" container/process. Finds none.
3.  **Provision:** Orchestrator signals a Worker Node to provision a new runtime.
4.  **Fetch & Load:** The Worker downloads the user's function code (e.g., from S3 or local storage) and starts the `runtime_host.py` process with the code path.
5.  **Initialization:** `runtime_host.py` dynamically imports the user function.
6.  **Execution:** Once ready, the Worker forwards the payload to the `runtime_host.py` HTTP server.
7.  **Response:** Result is returned up the chain to the client.

### B. Warm Start (Low Latency)
Occurs when a runtime is already active and idle (kept alive from a previous request).

1.  **Request:** API Gateway receives a request.
2.  **Lookup:** Orchestrator finds an idle runtime for this function in the Worker Pool.
3.  **Forward:** Orchestrator tells the Worker Node to send the payload directly to the existing `runtime_host.py` instance.
4.  **Execution:** The already-running process handles the request immediately.
5.  **Response:** Result is returned to the client.

## 3. Core Technology Decision & Justification

We compared **Container-based** (e.g., Docker) vs. **Process-based** (e.g., forking processes directly on the OS) execution layers.

| Feature | Container-Based | Process-Based |
| :--- | :--- | :--- |
| **Security Isolation** | **High.** Namespace and cgroup isolation. Harder to break out. | **Low.** Shared OS kernel and file system (unless chrooted). |
| **Resource Overhead** | **Medium.** Requires a container daemon and virtual network interfaces. | **Low.** Very minimal overhead; just memory for the interpreter. |
| **Cold Start Perf** | **Slower.** Must spin up container filesystem and networking (approx 500ms-2s). | **Fast.** Process creation is nearly instantaneous (approx 10-50ms). |
| **Impl. Complexity** | **High.** Requires managing container runtimes, networking bridges, and image registries. | **Low.** Uses standard OS system calls. |

### Recommendation
**Decision:** We recommend a **Process-based** approach for the AryaXAI internal platform.

**Justification:**
1.  **Performance:** The prompt specifies "maximum performance" and "lightweight." Processes have significantly faster start-up times than containers, eliminating the "Cold Start" penalty that plagues standard FaaS.
2.  **Simplicity:** As an internal tool, we do not have the same hostile multi-tenant security risks as a public cloud (like AWS). We can trust our internal developers more than public users.
3.  **Control:** Managing processes gives us granular control over memory and CPU without the abstraction layer of a container engine.

*Note: As the platform matures, we may move to microVMs (like Firecracker) for better isolation, but for the MVP, Process-based meets the "lightweight" requirement best.*
