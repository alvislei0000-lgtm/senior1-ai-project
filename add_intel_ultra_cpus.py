#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Intel Ultra series CPUs to hardware database
"""

import json

def add_intel_ultra_cpus():
    """
    Add Intel Ultra series CPUs to the hardware database
    """

    # Intel Ultra series CPUs data
    intel_ultra_cpus = [
        {
            "category": "cpu",
            "model": "Intel Core Ultra 9 285K",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 9 285",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 7 265K",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 7 265",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 7 258V",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 32
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 7 257K",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 5 245K",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 5 245",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 64
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 5 238V",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 32
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 5 235",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 32
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 5 225",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 32
        },
        {
            "category": "cpu",
            "model": "Intel Core Ultra 3 237",
            "generation": "Ultra",
            "release_year": 2024,
            "brand": "Intel",
            "vram_gb": 0,
            "ram_gb": 32
        }
    ]

    # Update backend data file
    update_hardware_data("backend/data/hardware_seed.json", intel_ultra_cpus)

    # Update frontend data file
    update_hardware_data("frontend/src/data/hardware_seed_frontend.json", intel_ultra_cpus)

    print(f"Successfully added {len(intel_ultra_cpus)} Intel Ultra series CPUs!")

def update_hardware_data(file_path, new_cpus):
    """
    Update hardware data file with new CPUs
    """
    # Read existing data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Separate CPUs and GPUs
    cpus = [item for item in data['items'] if item['category'] == 'cpu']
    gpus = [item for item in data['items'] if item['category'] == 'gpu']

    # Add new CPUs
    added_count = 0
    for new_cpu in new_cpus:
        # Check if already exists
        if not any(cpu['model'] == new_cpu['model'] for cpu in cpus):
            cpus.append(new_cpu)
            added_count += 1
            print(f"Added: {new_cpu['model']}")

    # Recombine data: GPUs first, then CPUs
    data['items'] = gpus + cpus

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Added {added_count} new CPUs to {file_path}")

if __name__ == "__main__":
    add_intel_ultra_cpus()



