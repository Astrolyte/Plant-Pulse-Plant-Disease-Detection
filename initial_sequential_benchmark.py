import os
import time
import numpy as np
import requests


URL = "http://127.0.0.1:8080/api/predict"
IMAGE_PATH = r"C:\Users\Aditya\Documents\Minor_Project\Tomato\Test\Healthy\0caff918-5807-40f2-b9e4-7dd34a7bab5d___RS_HL 0345.jpg"

REQUEST_COUNTS = [5, 10, 25, 50, 100, 250, 500]

warmup_requests = 25

def warmup():
    print("\n warming up the model...")
    
    for i in range(warmup_requests):
        response, latency = send_request(IMAGE_PATH)
        
    print("warmup complete.")

def send_request(image_path):
    with open(image_path, "rb") as image:
        start = time.perf_counter()
        response = requests.post(
            URL,
            files={
                "file": (
                    os.path.basename(image_path),
                    image,
                    "image/jpeg"
                )
            }
        )
        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        return response, latency_ms


def run_benchmark(num_requests):
    latencies = []
    errors = 0

    print("\n" + "=" * 60)
    print(f"Running {num_requests} requests")
    print("=" * 60)

    start_time = time.perf_counter()

    for i in range(num_requests):
        try:
            response, latency = send_request(IMAGE_PATH)
            latencies.append(latency)

            if response.status_code >= 400:
                errors += 1

            print(
                f"Request {i + 1:03d}/{num_requests} | "
                f"Status: {response.status_code} | "
                f"Latency: {latency:.2f} ms"
            )
        except requests.RequestException as e:
            errors += 1
            print(f"Request {i + 1:03d}/{num_requests} | ERROR: {e}")

    total_time = time.perf_counter() - start_time

    if not latencies:
        return None

    latencies = np.array(latencies)
    average = np.mean(latencies)
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    minimum = np.min(latencies)
    maximum = np.max(latencies)
    requests_per_second = len(latencies) / total_time if total_time > 0 else 0

    return {
        "requests": num_requests,
        "successful": len(latencies),
        "errors": errors,
        "total_time": total_time,
        "average": average,
        "p50": p50,
        "p95": p95,
        "p99": p99,
        "minimum": minimum,
        "maximum": maximum,
        "rps": requests_per_second,
    }


def print_summary_table(results):
    headers = [
        "Requests", "Success", "Errors", "Avg (ms)", "P50 (ms)",
        "P95 (ms)", "P99 (ms)", "Min (ms)", "Max (ms)", "Req/Sec"
    ]

    print("\n" + "=" * 140)
    print(f"{headers[0]:>8} {headers[1]:>8} {headers[2]:>8} {headers[3]:>10} "
          f"{headers[4]:>10} {headers[5]:>10} {headers[6]:>10} {headers[7]:>10} "
          f"{headers[8]:>10} {headers[9]:>10}")
    print("-" * 140)

    for result in results:
        print(
            f"{result['requests']:>8} "
            f"{result['successful']:>8} "
            f"{result['errors']:>8} "
            f"{result['average']:>10.2f} "
            f"{result['p50']:>10.2f} "
            f"{result['p95']:>10.2f} "
            f"{result['p99']:>10.2f} "
            f"{result['minimum']:>10.2f} "
            f"{result['maximum']:>10.2f} "
            f"{result['rps']:>10.2f}"
        )


if __name__ == "__main__":
    results = []
    warmup()
    for count in REQUEST_COUNTS:
        result = run_benchmark(count)
        if result:
            results.append(result)
            print(result)
            
    print_summary_table(results)