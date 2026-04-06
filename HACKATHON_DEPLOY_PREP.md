# 🚀 TacticalTriage: Hackathon Deployment Checklist

Please provide theFollowing information to **Santhosh** (or your developer friend) to complete the final deployment of the **TacticalTriage OpenEnv** project.

---

### 1. Mandatory Hugging Face Credentials
To push the project to Hugging Face Spaces (required for the Meta x HF OpenEnv Hackathon):

*   **HF Username**: Your exact Hugging Face handle (e.g., `your-username`).
*   **HF Write Token**: A token with **Write** or **Fine-grained** access (scoped to yours or your organization's Space).
    *   *Where to get it:* [Hugging Face Settings -> Tokens](https://huggingface.co/settings/tokens).

### 2. Mandatory LLM API Credentials
To run the `inference.py` script (the part where the AI agent "plays" the environment):

*   **HF Token**: The same token as above (used to call the inference router at `router.huggingface.co/v1`).
*   **Model ID**: The exact model string to use (Default: `Qwen/Qwen2.5-72B-Instruct`).

### 3. GitHub Remote URL (Optional)
If you want the source code backed up on GitHub:

*   **Repo URL**: The "new" repository URL you just created (e.g., `https://github.com/your-username/tactical-triage.git`).

---

### How to use this information:
Once you have these, paste them into the chat and Santhosh will:
1.  **Finalize Git**: Run `git remote add origin <GitHub URL>`.
2.  **Push Code**: Run `git push -u origin main`.
3.  **HF Push**: Run `openenv push --repo-id <Username>/tactical-triage`.
4.  **Inference Check**: Execute a live run of the agent against your new Space.
