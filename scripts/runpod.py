# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "dotenv",
#     "httpx",
# ]
# ///
import httpx
import os
import time
import signal
import sys
import json
from dotenv import load_dotenv

load_dotenv()

def create_pod(api_key: str):
    """Creates a new pod on RunPod."""
    url = "https://rest.runpod.io/v1/pods"
    
    payload = {
        "cloudType": "COMMUNITY",
        "computeType": "GPU",
        "gpuCount": 1,
        "allowedCudaVersions": ["12.8"],
        "volumeInGb": 0,
        "containerDiskInGb": 50,
        "gpuTypeIds": ["NVIDIA GeForce RTX 3090"],
        "imageName": "vllm/vllm-openai:latest",
        "name": "vllm",
        "ports": ["8000/http", "22/tcp"],
        "supportPublicIp": True,
        "dockerStartCmd": ["--model", "Qwen/Qwen3-4B", "--enable-auto-tool-choice", "--tool-call-parser", "hermes", "--max-model-len", "8128"],
        "interruptible": False,
        "locked": False,
        "minDownloadMbps": 800,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = httpx.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def terminate_pod(api_key: str, pod_id: str):
    """Terminates a pod on RunPod."""
    print(f"Requesting termination for pod {pod_id}...")
    url = f"https://rest.runpod.io/v1/pods/{pod_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = httpx.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Pod {pod_id} terminated successfully.")
        if response.text:
            print("Response:", json.dumps(response.json(), indent=2))
    except httpx.HTTPStatusError as e:
        print(f"Failed to terminate pod {pod_id}: {e}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred during termination: {e}", file=sys.stderr)


pod_id = None
api_key = os.environ.get("RUNPOD_API_KEY")

def cleanup(sig, frame):
    global pod_id, api_key
    print("\nCtrl+C detected. Initiating cleanup...")
    if pod_id and api_key:
        terminate_pod(api_key, pod_id)
    else:
        print("No pod to terminate.")
    sys.exit(0)

def main():
    global pod_id, api_key
    if not api_key:
        print("Error: RUNPOD_API_KEY environment variable not set.")
        sys.exit(1)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    try:
        print("Creating pod...")
        pod_data = create_pod(api_key)
        pod_id = pod_data.get("id")
        if pod_id:
            print(f"Pod created successfully with ID: {pod_id}")
            print("Pod details:", json.dumps(pod_data, indent=2))
        else:
            print("Failed to get pod ID from response.")
            print("Response:", json.dumps(pod_data, indent=2))
            sys.exit(1)

        print("\nPod is running. Press Ctrl+C to terminate.")
        while True:
            time.sleep(5)

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
