def map_band_aliases(dataset, source):
    """Standardize band names across different satellite sources."""
    band_aliases = {
        "sentinel": {
            "blue": "blue",
            "red": "red",
            "green": "green",
            "nir": "nir",
            "swir16": "swir16",
            "swir22": "swir22",
            "scl": "scl"
        },
        "landsat": {
            "blue": "blue",
            "red": "red",
            "green": "green",
            "nir": "nir08",  # Landsat uses "nir08"
            "swir16": "swir16",
            "swir22": "swir22"
        }
    }

    if source not in band_aliases:
        raise ValueError(f"Unsupported dataset source: {source}")

    alias_map = band_aliases[source]

    # Rename bands if they exist in the dataset
    rename_dict = {alias_map[key]: key for key in alias_map if alias_map[key] in dataset}

    return dataset.rename(rename_dict)
