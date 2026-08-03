from rich.console import Console
from rich.markdown import Markdown

text = """
| Phase | Core Risk Focus | Key Action Item | Technology/Technique Used |
| :--- | :--- | :--- | :--- |
| Data Prep | Privacy / Leakage | Securely anonymize and audit all training data. | Differential Privacy (DP), Anonymization |
| Training | Model Integrity / Poisoning | Ensure the integrity of the process and artifacts. | Cryptographic Hashing, Immutable Registries |
| Testing | Adversarial Attacks | Test robustness against malicious inputs. | Adversarial Training, Red Teaming |
| Deployment | Governance / Compliance | Establish clear rules for use and accountability. | GRC Frameworks, Access Control (RBAC) |
| Monitoring | Drift / New Attacks | Continuously monitor performance in the live environment. | Continuous Monitoring, Anomaly Detection |
"""
print("chatgpt fix")
Console().print(Markdown(text))

text = """
## Summary Table\n\n| Focus Area | Key Challenge | Optimization/Security Strategy\
    \ | Tools/Techniques |\n| :--- | :--- | :--- | :--- |\n| **Performance** | High\
    \ Latency, Low Throughput | Quantization, Pruning, Batching | TensorRT, ONNX,\
    \ GPU Acceleration |\n| **API Security** | Model Manipulation (Prompt Injection)\
    \ | Input Validation, Guardrails, Output Filtering | Input Sandboxing, Reinforcement\
    \ Learning from Human Feedback (RLHF) |\n| **Data Security** | Data Exfiltration\
    \ Risk | Strict RBAC, Network Policies, Secrets Management | Docker Least Privilege,\
    \ Vault/KMS |\n| **Deployment** | Vulnerable Environment | Multi-Stage Builds,\
    \ Resource Limits | Docker, Kubernetes, NetworkPolicies |
"""
print("straight from lesson file")
Console().print(Markdown(text))