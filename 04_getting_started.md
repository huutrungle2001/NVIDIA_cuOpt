# NVIDIA cuOpt: Getting Started Guide

There are multiple pathways to evaluate, develop, and deploy decision optimization applications using NVIDIA cuOpt.

---

## 1. Quick Evaluation (Free & Low-Barrier)

*   **Google Colab Notebooks:** 
    *   The easiest way to write Python code and call cuOpt without setting up local GPU environments.
    *   NVIDIA provides ready-to-run Jupyter notebooks showing routing and scheduling examples.
    *   *Link:* [Try cuOpt on Google Colab](https://colab.research.google.com/github/NVIDIA/cuopt-examples/blob/cuopt_examples_launcher/cuopt_examples_launcher.ipynb)
*   **NVIDIA API Catalog:**
    *   Access hosted cuOpt microservices directly via web APIs to test and solve vehicle routing problems (VRP) or linear programming problems using pre-built web UIs.
    *   *Link:* [NVIDIA Build API Catalog](https://build.nvidia.com/nvidia/nvidia-cuopt)

---

## 2. Developer Installation Options

For developers setting up local, hybrid, or cloud development pipelines:

*   **PIP:** Install directly into Python environments (supports Linux systems with NVIDIA GPUs and CUDA).
    ```bash
    pip install cuopt
    ```
*   **Conda:** Available via the RAPIDS conda channel.
    ```bash
    conda install -c rapidsai-nightly cuopt-server
    ```
*   **Docker Containers:** Pre-packaged docker images hosting the cuOpt server are available on Docker Hub and NVIDIA NGC.
    *   *NGC Path:* `catalog.ngc.nvidia.com/orgs/nvidia/teams/cuopt/containers/cuopt`
*   **GitHub Repository:** Access source files, sample scripts, and local setup configurations.
    *   *Link:* [NVIDIA cuOpt GitHub Repository](https://github.com/NVIDIA/cuopt)

---

## 3. Scale Tiers and Constraints

The capability limits vary depending on the deployment tier:

| Deployment Tier | Max VRP Locations | Supported Methods | Best For |
| :--- | :---: | :---: | :--- |
| **API Catalog (Free/Demo)** | Up to 1,000 | VRP, TSP, PDP | Prototyping, small tests |
| **NVIDIA LaunchPad (Trial)** | 10,000 - 15,000 | LP, MIP, VRP, QP | Enterprise trial evaluation |
| **NVIDIA AI Enterprise (Prod)** | 15,000+ | Full features (LP, MIP, VRP, QP) | Production workloads, SLA support |

---

## 4. Production Licensing

*   **NVIDIA LaunchPad:** Request sandbox access to try cuOpt on enterprise-grade hardware without committing to purchases.
*   **90-Day Trial License:** Request temporary access to run cuOpt containers locally or in your private cloud.
*   **NVIDIA AI Enterprise:** The commercial version for large-scale operations requiring security patching, LTS releases, and 24/7 technical support.

---

*Related Documents:*
- [**00. Executive Summary**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/00_summary.md)
- [**01. Overview & Core Capabilities**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/01_overview.md)
- [**02. Key Benefits**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/02_benefits.md)
- [**03. Real-World Use Cases**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/03_use_cases.md)
- [**README Index**](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/README.md)
