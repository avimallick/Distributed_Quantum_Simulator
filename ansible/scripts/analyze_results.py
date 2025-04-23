if __name__ == "__main__":
    with open("/mnt/simulation_data/results.txt", "r") as f:
        results = [eval(line.strip()) for line in f]
    for i, result in enumerate(results):
        print(f"Circuit {i + 1}: {result}")