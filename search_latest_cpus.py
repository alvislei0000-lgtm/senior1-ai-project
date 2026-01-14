#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Google搜索获取最新CPU信息并添加到硬件数据库
"""

import json
import os
import re
import sys
from google_programmable_search import google_search

def extract_cpu_info_from_search_results(results):
    """
    Extract CPU information from search results
    """
    cpus = []

    # 从搜索结果中提取信息
    for result in results:
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()

        # Check for CPU-related keywords
        if any(keyword in title + snippet for keyword in ['cpu', 'processor', 'core', 'ryzen']):
            # Try to match Intel CPU
            if 'intel' in title + snippet:
                # 14th Gen or higher
                gen_match = re.search(r'(\d{1,2})(?:th|rd|nd|st)\s+gen', title + snippet)
                if gen_match:
                    gen_num = int(gen_match.group(1))
                    if gen_num >= 14:  # Focus on 14th gen and newer CPUs
                        # Extract specific model
                        model_match = re.search(r'(i[3579]-(\d{4,5}[A-Z]*))', title + snippet, re.IGNORECASE)
                        if model_match:
                            model = f"Intel Core {model_match.group(1)}"
                            generation = f"{gen_num}th Gen"
                            brand = "Intel"
                            release_year = 2024 if gen_num == 14 else 2025

                            # Estimate memory support
                            ram_gb = 32 if 'i9' in model or 'i7' in model else 16

                            cpu_info = {
                                "category": "cpu",
                                "model": model,
                                "generation": generation,
                                "release_year": release_year,
                                "brand": brand,
                                "vram_gb": 0,
                                "ram_gb": ram_gb
                            }

                            # Check if already exists
                            if not any(cpu['model'] == model for cpu in cpus):
                                cpus.append(cpu_info)

            # Try to match AMD CPU
            elif 'amd' in title + snippet or 'ryzen' in title + snippet:
                # Zen 5 or higher
                zen_match = re.search(r'zen\s+(\d)', title + snippet, re.IGNORECASE)
                if zen_match:
                    zen_num = int(zen_match.group(1))
                    if zen_num >= 5:  # Focus on Zen 5 and newer CPUs
                        # Extract specific model
                        model_match = re.search(r'ryzen\s+(\d)\s+(\d{4,5}[A-Z]*)', title + snippet, re.IGNORECASE)
                        if model_match:
                            series = model_match.group(1)
                            model_num = model_match.group(2)
                            model = f"AMD Ryzen {series} {model_num}"
                            generation = f"Zen {zen_num}"
                            brand = "AMD"
                            release_year = 2024 if zen_num == 5 else 2025

                            # Estimate memory support
                            ram_gb = 32 if series in ['9', '7'] else 16

                            cpu_info = {
                                "category": "cpu",
                                "model": model,
                                "generation": generation,
                                "release_year": release_year,
                                "brand": brand,
                                "vram_gb": 0,
                                "ram_gb": ram_gb
                            }

                            # Check if already exists
                            if not any(cpu['model'] == model for cpu in cpus):
                                cpus.append(cpu_info)

    return cpus

def search_latest_cpus():
    """
    Search for latest CPU information
    """
    print("Searching for latest CPU information...")

    # 搜索查询
    queries = [
        "latest Intel 14th gen CPUs 2024",
        "AMD Ryzen 8000 series Zen 5 processors",
        "new CPU releases 2024 2025",
        "Intel Core Ultra 200V series",
        "AMD Ryzen 9000 series Zen 5"
    ]

    all_cpus = []

    for query in queries:
        print(f"Searching: {query}")
        try:
            results = google_search(query, "AIzaSyAzwW9QWKJA3f0XH-ebTg34M49nzXv7KhU", "034784ab1b1404dc2", num=8)
            if results:
                cpus = extract_cpu_info_from_search_results(results)
                all_cpus.extend(cpus)
                print(f"Found {len(cpus)} potential CPU entries")
            else:
                print("No search results")
        except Exception as e:
            print(f"Search failed: {e}")
        print()

    # 去重
    unique_cpus = []
    seen_models = set()
    for cpu in all_cpus:
        if cpu['model'] not in seen_models:
            unique_cpus.append(cpu)
            seen_models.add(cpu['model'])

    return unique_cpus

def add_cpus_to_hardware_data(new_cpus, file_path="backend/data/hardware_seed.json"):
    """
    Add new CPUs to hardware data file
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

    print(f"\nAdded {added_count} new CPUs to {file_path}")

def add_cpus_to_frontend_data(new_cpus, file_path="frontend/src/data/hardware_seed_frontend.json"):
    """
    Add new CPUs to frontend hardware data file
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
    print("Starting to search and add latest CPU information...\n")

    # 搜索最新的CPU
    new_cpus = search_latest_cpus()

    if not new_cpus:
        print("No new CPU information found")
        return

    print(f"Found {len(new_cpus)} new CPUs:")
    for cpu in new_cpus:
        print(f"  - {cpu['model']} ({cpu['generation']}, {cpu['release_year']})")

    print("\n" + "="*50)

    # Add to backend data file
    add_cpus_to_hardware_data(new_cpus)

    # Add to frontend data file
    add_cpus_to_frontend_data(new_cpus)

    print(f"\nCompleted! Added {len(new_cpus)} new CPU entries in total")

if __name__ == "__main__":
    main()
