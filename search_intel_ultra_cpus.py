#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search for Intel Ultra series CPUs using Google search and add to hardware database
"""

import json
import re
from google_programmable_search import google_search

def extract_intel_ultra_cpus_from_results(results):
    """
    Extract Intel Ultra CPU information from search results
    """
    cpus = []

    for result in results:
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        full_text = title + ' ' + snippet

        # Look for Intel Ultra CPU patterns
        if 'intel' in full_text and ('ultra' in full_text or 'core ultra' in full_text):
            # Extract Ultra CPU models
            ultra_patterns = [
                r'intel core ultra (\d+)\s+(\d+[a-z]*)',
                r'intel core ultra (\d+)\s+(\d+)',
                r'core ultra (\d+)\s+(\d+[a-z]*)',
                r'ultra (\d+)\s+(\d+[a-z]*)'
            ]

            for pattern in ultra_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    series = match[0]  # Like 9, 7, 5, 3
                    model = match[1]   # Like 285K, 265, 245K, etc.

                    cpu_model = f"Intel Core Ultra {series} {model}"

                    # Determine RAM support based on series
                    ram_gb = 64 if series in ['9', '7'] else 32

                    cpu_info = {
                        "category": "cpu",
                        "model": cpu_model,
                        "generation": "Ultra",
                        "release_year": 2024,  # Ultra series released in 2024
                        "brand": "Intel",
                        "vram_gb": 0,
                        "ram_gb": ram_gb
                    }

                    # Check if already exists (avoid duplicates)
                    if not any(cpu['model'].lower() == cpu_model.lower() for cpu in cpus):
                        cpus.append(cpu_info)

    return cpus

def search_intel_ultra_cpus():
    """
    Search for Intel Ultra series CPUs
    """
    print("Searching for Intel Ultra series CPUs...")

    # Search queries for Intel Ultra CPUs
    queries = [
        "Intel Core Ultra 9 processors 2024",
        "Intel Core Ultra 7 series CPUs",
        "Intel Core Ultra 5 laptop processors",
        "Intel Core Ultra 3 chips specifications",
        "Intel Meteor Lake Ultra CPUs list",
        "Intel Arrow Lake Ultra processors"
    ]

    all_cpus = []

    for query in queries:
        print(f"Searching: {query}")
        try:
            results = google_search(query, "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU", "034784ab1b1404dc2", num=10)
            if results:
                cpus = extract_intel_ultra_cpus_from_results(results)
                all_cpus.extend(cpus)
                print(f"Found {len(cpus)} potential Ultra CPUs")
            else:
                print("No search results")
        except Exception as e:
            print(f"Search failed: {e}")
        print()

    # Remove duplicates
    unique_cpus = []
    seen_models = set()
    for cpu in all_cpus:
        model_key = cpu['model'].lower()
        if model_key not in seen_models:
            unique_cpus.append(cpu)
            seen_models.add(model_key)

    return unique_cpus

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
        if not any(cpu['model'].lower() == new_cpu['model'].lower() for cpu in cpus):
            cpus.append(new_cpu)
            added_count += 1
            print(f"Added: {new_cpu['model']}")

    # Recombine data: GPUs first, then CPUs
    data['items'] = gpus + cpus

    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Added {added_count} new CPUs to {file_path}")

def main():
    """
    Main function
    """
    print("Starting to search for Intel Ultra series CPUs...\n")

    # Search for Intel Ultra CPUs
    new_cpus = search_intel_ultra_cpus()

    if not new_cpus:
        print("No new Intel Ultra CPUs found")
        return

    print(f"Found {len(new_cpus)} new Intel Ultra CPUs:")
    for cpu in new_cpus:
        print(f"  - {cpu['model']} ({cpu['generation']}, {cpu['release_year']})")

    print("\n" + "="*50)

    # Update backend data file
    update_hardware_data("backend/data/hardware_seed.json", new_cpus)

    # Update frontend data file
    update_hardware_data("frontend/src/data/hardware_seed_frontend.json", new_cpus)

    print(f"\nCompleted! Added {len(new_cpus)} Intel Ultra CPUs in total")

if __name__ == "__main__":
    main()



