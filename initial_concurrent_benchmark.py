import os
import time
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor


# ============================================================
# Configuration
# ============================================================

URL = "http://127.0.0.1:8080/api/predict"

IMAGE_PATH = r"C:\Users\Aditya\Documents\Minor_Project\Tomato\Test\Healthy\0caff918-5807-40f2-b9e4-7dd34a7bab5d___RS_HL 0345.jpg"

# Simulated concurrent users
USER_LIST = [10, 25, 50, 100, 150, 200]

# Requests made by each user
REQUESTS_PER_USER = [5, 10, 20, 50]

WARMUP_REQUESTS = 25

# ============================================================
# Load image once
# ============================================================

with open(IMAGE_PATH, "rb") as image:
    IMAGE_BYTES = image.read()

IMAGE_NAME = os.path.basename(IMAGE_PATH)

# Send request


def send_single_request():
    start = time.perf_counter()

    try:
        response = requests.post(
            URL,
            files={
                "file": (
                    IMAGE_NAME,
                    IMAGE_BYTES,
                    "image/jpeg",
                )
            },
            timeout=60,
        )

        latency_ms = (time.perf_counter() - start) * 1000
        return response, latency_ms

    except requests.RequestException:
        return None, None


# ============================================================
# Simulate one user
# ============================================================

def simulate_user_request(num_requests):
    latencies = []

    for _ in range(num_requests):
        response, latency_ms = send_single_request()

        if response is not None and latency_ms is not None:
            if response.status_code < 400:
                latencies.append(latency_ms)

    return latencies


# ============================================================
# Warmup
# ============================================================

def warmup():
    print("\nWarming up model...")

    for i in range(WARMUP_REQUESTS):
        try:
            start = time.perf_counter()
            response = requests.post(
                URL,
                files={
                    "file": (
                        IMAGE_NAME,
                        IMAGE_BYTES,
                        "image/jpeg",
                    )
                },
                timeout=60,
            )
            latency_ms = (time.perf_counter() - start) * 1000

            print(
                f"Warmup {i + 1:02d}/{WARMUP_REQUESTS} "
                f"| Status: {response.status_code} | {latency_ms:.2f} ms"
            )

        except requests.RequestException as e:
            print(f"Warmup failed: {e}")

    print("Warmup complete.\n")


# ============================================================
# Run load test
# ============================================================

def run_load_test(concurrent_users, requests_per_user):
    # print(
    #     f"Running {concurrent_users} users × {requests_per_user} requests/user"
    # )

    total_requests = concurrent_users * requests_per_user
    start_test = time.perf_counter()
    all_latencies = []

    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [
            executor.submit(simulate_user_request, requests_per_user)
            for _ in range(concurrent_users)
        ]

        for future in futures:
            try:
                latencies = future.result()
                all_latencies.extend(latencies)
            except Exception as e:
                print(f"User failed: {e}")

    total_duration = time.perf_counter() - start_test

    if not all_latencies:
        return None

    latencies = np.array(all_latencies)
    successful_requests = len(latencies)
    errors = total_requests - successful_requests

    average_latency = np.mean(latencies)
    p50_latency = np.percentile(latencies, 50)
    p95_latency = np.percentile(latencies, 95)
    p99_latency = np.percentile(latencies, 99)
    minimum_latency = np.min(latencies)
    maximum_latency = np.max(latencies)
    throughput = successful_requests / total_duration if total_duration > 0 else 0

    return {
        "users": concurrent_users,
        "requests_per_user": requests_per_user,
        "total_requests": total_requests,
        "successful": successful_requests,
        "errors": errors,
        "average": average_latency,
        "p50": p50_latency,
        "p95": p95_latency,
        "p99": p99_latency,
        "minimum": minimum_latency,
        "maximum": maximum_latency,
        "throughput": throughput,
    }



# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 100)
    print("PlantPulse Concurrent User Load Test")
    print("=" * 100)

    warmup()

    results = []
    
    print(
        f"{'Users':<8} | "
        f"{'Req/User':<9} | "
        f"{'Total':<8} | "
        f"{'Avg Latency':<14} | "
        f"{'P50 Latency':<14} | "
        f"{'P95 Latency':<14} | "
        f"{'P99 Latency':<14} | "
        f"{'Throughput':<12} | "
        f"{'Errors':<8}"
    )

    print("-" * 125)

    for users in USER_LIST:
        for requests_per_user in REQUESTS_PER_USER:
            result = run_load_test(users, requests_per_user)
            if result:
                results.append(result)
                print(
                    f"{result['users']:<8} | "
                    f"{result['requests_per_user']:<9} | "
                    f"{result['total_requests']:<8} | "
                    f"{result['average']:<14.2f} | "
                    f"{result['p50']:<14.2f} | "
                    f"{result['p95']:<14.2f} | "
                    f"{result['p99']:<14.2f} | "
                    f"{result['throughput']:<12.2f} | "
                    f"{result['errors']:<8}"
                )