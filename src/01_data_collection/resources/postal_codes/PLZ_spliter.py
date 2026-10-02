from pathlib import Path

import pandas as pd
import numpy as np

def balanced_split(data, sort_by, n):
    # Sort by population descending
    sorted_data = data.sort_values(by=sort_by, ascending=False).copy()

    # Initialize empty chunks
    chunks = [[] for _ in range(n)]
    chunk_populations = [0] * n  # Keep track of population per chunk

    # Distribute ZIP codes across chunks
    for _, row in sorted_data.iterrows():
        min_idx = np.argmin(chunk_populations)  # Find the chunk with the smallest population
        chunks[min_idx].append(row["PLZ"])  # Assign ZIP to that chunk
        chunk_populations[min_idx] += row[sort_by]  # Update chunk population

    # Convert to DataFrame output
    zip_to_chunk = {zip_code: i for i, chunk in enumerate(chunks) for zip_code in chunk}
    data["chunk"] = data["PLZ"].map(zip_to_chunk)

    return population_data

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent
    population_data = pd.read_csv(base_dir / "population_by_plz.csv", delimiter=",")

    # Split into n chunks
    result = balanced_split(population_data, "Population in 2022", 4)
    print(result)
    print(list(set(result["chunk"])))

    result.to_csv(base_dir / "split_population_data.csv", index=False)