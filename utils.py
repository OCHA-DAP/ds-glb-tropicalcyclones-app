import os

import numpy as np
import psutil


def calc_plotly_zoom(lon_min, lat_min, lon_max, lat_max) -> float:
    """Calculate the zoom level for a plotly mapbox map based on GeoDataFrame extent"""
    lon_zoom_range = np.array(
        [
            0.0007,
            0.0014,
            0.003,
            0.006,
            0.012,
            0.024,
            0.048,
            0.096,
            0.192,
            0.3712,
            0.768,
            1.536,
            3.072,
            6.144,
            11.8784,
            23.7568,
            47.5136,
            98.304,
            190.0544,
            360.0,
        ]
    )
    width_to_height = 1
    margin = 1.8
    height = (lat_max - lat_min) * margin * width_to_height
    width = (lon_max - lon_min) * margin
    lon_zoom = np.interp(width, lon_zoom_range, range(20, 0, -1))
    lat_zoom = np.interp(height, lon_zoom_range, range(20, 0, -1))
    zoom = round(min(lon_zoom, lat_zoom), 2)
    return zoom


def get_memory_usage() -> float:
    """Get the memory usage of the current process in MB"""
    # Get the current process ID
    pid = os.getpid()
    # Get the Process object
    process = psutil.Process(pid)
    # Get the memory info
    mem_info = process.memory_info()
    # Calculate the memory usage in MB
    memory_usage = mem_info.rss / 1024 / 1024
    return memory_usage


def print_memory_usage() -> None:
    """Print the memory usage of the current process in MB"""
    memory_usage = get_memory_usage()
    print(f"Memory usage: {memory_usage:.2f} MB")
