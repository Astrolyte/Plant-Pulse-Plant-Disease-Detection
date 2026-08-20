import os
import time
import requests
import numpy as np
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
URL = "http://127.0.0.1:8080/api/predict"
IMAGE_DIRECTORY = r"C:\Users\Aditya\Documents\Minor_Project\Tomato\Test"
CONCURRENCY_LEVELS = [1, 5, 10, 25, 50, 100]
REQUESTS_PER_LEVEL = 100

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


# Load images
def load_images():
    images = []

    for root, _, files in os.walk(IMAGE_DIRECTORY):
        for filename in files:
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                path = os.path.join(root, filename)

                with open(path, "rb") as f:
                    images.append((filename, f.read()))

    print(f"Loaded {len(images)} images.")
    return images


# Clear Redis
def clear_cache():
    redis_client.flushdb()


# Send request
def send_request(image_name, image_bytes):
    start = time.perf_counter()

    try:
        response = requests.post(
            URL,
            files={"file": (image_name, image_bytes, "image/jpeg")},
            timeout=60
        )

        latency = (time.perf_counter() - start) * 1000

        try:
            data = response.json()
        except Exception:
            data = {}

        metadata = data.get("metadata", {})

        return {
            "success": response.status_code < 400,
            "latency": latency,
            "cache_hit": metadata.get("cache_hit", False),
            "status": response.status_code,
            "error": data.get("error")
        }

    except requests.RequestException as e:
        latency = (time.perf_counter() - start) * 1000

        return {
            "success": False,
            "latency": latency,
            "cache_hit": False,
            "status": None,
            "error": str(e)
        }


# Populate cache
def populate_cache(image):
    result = send_request(image[0], image[1])

    if not result["success"]:
        print(
            f"Cache population failed | "
            f"Status={result['status']} | "
            f"Error={result['error']}"
        )

        return False

    return True


# Run concurrent requests
def run_requests(request_images, concurrency):
    results = []

    start_test = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:

        futures = [
            executor.submit(
                send_request,
                image[0],
                image[1]
            )
            for image in request_images
        ]

        for future in as_completed(futures):
            results.append(future.result())

    total_time = time.perf_counter() - start_test

    return results, total_time


# Calculate metrics
def calculate_metrics(results, total_time):
    latencies = np.array([
        result["latency"]
        for result in results
    ])

    successful = sum(
        result["success"]
        for result in results
    )

    errors = len(results) - successful

    cache_hits = sum(
        result["cache_hit"]
        for result in results
    )

    cache_misses = successful - cache_hits

    return {
        "total": len(results),
        "successful": successful,
        "errors": errors,
        "avg": np.mean(latencies),
        "p50": np.percentile(latencies, 50),
        "p95": np.percentile(latencies, 95),
        "p99": np.percentile(latencies, 99),
        "min": np.min(latencies),
        "max": np.max(latencies),
        "throughput": len(results) / total_time,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "hit_rate": (
            cache_hits / successful * 100
            if successful else 0
        )
    }


# 1. Cache MISS
def benchmark_miss(images, concurrency):
    clear_cache()

    request_images = images[:REQUESTS_PER_LEVEL]

    results, total_time = run_requests(
        request_images,
        concurrency
    )

    return calculate_metrics(
        results,
        total_time
    )


# 2. Cache HIT
def benchmark_hit(images, concurrency):
    clear_cache()

    if not populate_cache(images[0]):
        return None

    request_images = [
        images[0]
        for _ in range(REQUESTS_PER_LEVEL)
    ]

    results, total_time = run_requests(
        request_images,
        concurrency
    )

    return calculate_metrics(
        results,
        total_time
    )


# 3. Mixed workload
def benchmark_mixed(images, concurrency):
    clear_cache()

    hit_count = 70
    miss_count = REQUESTS_PER_LEVEL - hit_count

    hit_image = images[0]

    if not populate_cache(hit_image):
        return None

    miss_images = images[1:miss_count + 1]

    request_images = []

    for i in range(REQUESTS_PER_LEVEL):

        if i < hit_count:
            request_images.append(hit_image)
        else:
            request_images.append(
                miss_images[i - hit_count]
            )

    np.random.shuffle(request_images)

    results, total_time = run_requests(
        request_images,
        concurrency
    )

    return calculate_metrics(
        results,
        total_time
    )


# Print results
def print_results(results, mode):
    print(f"\nREDIS BENCHMARK — {mode}")
    print("-" * 130)

    print(
        f"{'Conc.':>8} "
        f"{'Total':>8} "
        f"{'Avg':>10} "
        f"{'P50':>10} "
        f"{'P95':>10} "
        f"{'P99':>10} "
        f"{'RPS':>10} "
        f"{'Hits':>8} "
        f"{'Miss':>8} "
        f"{'Hit %':>8} "
        f"{'Errors':>8}"
    )

    print("-" * 130)

    for concurrency, result in results:

        if result is None:
            continue

        print(
            f"{concurrency:>8} "
            f"{result['total']:>8} "
            f"{result['avg']:>10.2f} "
            f"{result['p50']:>10.2f} "
            f"{result['p95']:>10.2f} "
            f"{result['p99']:>10.2f} "
            f"{result['throughput']:>10.2f} "
            f"{result['cache_hits']:>8} "
            f"{result['cache_misses']:>8} "
            f"{result['hit_rate']:>7.2f}% "
            f"{result['errors']:>8}"
        )


if __name__ == "__main__":

    images = load_images()

    if len(images) < REQUESTS_PER_LEVEL + 1:
        print(
            f"ERROR: Need at least "
            f"{REQUESTS_PER_LEVEL + 1} images."
        )
        exit()

    print(f"\nImages available: {len(images)}")
    print(f"Concurrency levels: {CONCURRENCY_LEVELS}")
    print(f"Requests per level: {REQUESTS_PER_LEVEL}")


    # 1. Cache MISS
    miss_results = []

    for concurrency in CONCURRENCY_LEVELS:
        print(f"\nMISS | Concurrency={concurrency}")

        result = benchmark_miss(
            images,
            concurrency
        )

        miss_results.append(
            (concurrency, result)
        )

    print_results(
        miss_results,
        "100% CACHE MISS"
    )


    # 2. Cache HIT
    hit_results = []

    for concurrency in CONCURRENCY_LEVELS:
        print(f"\nHIT | Concurrency={concurrency}")

        result = benchmark_hit(
            images,
            concurrency
        )

        hit_results.append(
            (concurrency, result)
        )

    print_results(
        hit_results,
        "100% CACHE HIT"
    )


    # 3. Mixed workload
    mixed_results = []

    for concurrency in CONCURRENCY_LEVELS:
        print(f"\nMIXED | Concurrency={concurrency}")

        result = benchmark_mixed(
            images,
            concurrency
        )

        mixed_results.append(
            (concurrency, result)
        )

    print_results(
        mixed_results,
        "70% HIT / 30% MISS"
    )