# cuOpt Sample Project: Capacitated Vehicle Routing Problem (CVRP)

This project contains a sample Python script showing how to model and solve a Capacitated Vehicle Routing Problem (CVRP) using the NVIDIA cuOpt Python API.

---

## The Optimization Problem Structure

*   **1 Depot (Node 0):** The central warehouse where all vehicles start and end their routes.
*   **3 Client Locations:**
    *   Node 1 (Store A): Demands 15 units.
    *   Node 2 (Store B): Demands 30 units.
    *   Node 3 (Store C): Demands 20 units.
*   **Fleet:** 2 vehicles, each with a maximum capacity of **40 units**.
*   **Distance Matrix:**
    $$\begin{pmatrix}
    0.0 & 10.0 & 15.0 & 20.0 \\
    10.0 & 0.0 & 35.0 & 25.0 \\
    15.0 & 35.0 & 0.0 & 30.0 \\
    20.0 & 25.0 & 30.0 & 0.0
    \end{pmatrix}$$

Because total demand is $15 + 30 + 20 = 65$ units, and each vehicle can only carry $40$ units, the solver must intelligently partition the orders across both trucks to minimize the total travel distance.

---

## How to Run This Project

NVIDIA cuOpt relies on GPU acceleration, requiring a system with an **NVIDIA GPU** and compatible CUDA drivers.

### Option A: Run in Google Colab (Recommended for Mac/CPU users)

If you are on a Mac or a machine without an NVIDIA GPU, you can run this script for free in the cloud:

1.  Open **[Google Colab](https://colab.research.google.com/)**.
2.  Change your runtime type to **T4 GPU** (Runtime $\rightarrow$ Change runtime type $\rightarrow$ T4 GPU).
3.  Install the cuOpt library and dependency stack:
    ```python
    !pip install cudf-cu12 cuopt-cu12 --extra-index-url=https://pypi.nvidia.com
    ```
4.  Copy the code from [solve_vrp.py](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/sample_project/solve_vrp.py) into a cell and execute it.

### Option B: Run via Docker (For GPU-enabled Linux systems)

If you have a local Linux machine with an NVIDIA GPU, you can run it inside the pre-built RAPIDS/cuOpt container:

1.  Pull and start the NGC container:
    ```bash
    docker run --gpus all -it --rm -v $(pwd):/workspace nvcr.io/nvidia/cuopt/cuopt:25.08.0-cuda12.8-py3.12
    ```
2.  Run the script:
    ```bash
    python /workspace/solve_vrp.py
    ```
