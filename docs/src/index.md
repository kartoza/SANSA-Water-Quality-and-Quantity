<!--
title: Water Quantity and Quality Monitoring Platform
summary: A Django EO analytics platform for monitoring and forecasting water quantity and quality across South Africa.
    - Dimas Ciputra
    - Zulfikar Muzakki
    - Juanique Voogt
    - Jeff Osundwa 
date: DATE
project_url: [PROJECT_GITHUB_URL](https://github.com/kartoza/SANSA-Water-Quality-and-Quantity)
copyright: Copyright 2025, SANSA
contact: -
license: This program is free software; you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.
-->

# Water Quantity and Quality Monitoring Platform

A decision-support platform for near real-time monitoring of water surface area and quality in South Africa using remote sensing and in-situ data.

## Introduction

Water resources are under threat due to climate change, pollution, and increased demand. This project provides a robust, scalable solution to track water quality and quantity over time using satellite data (Sentinel-2, Landsat), geospatial processing, and modern backend frameworks like Django and Celery.

The platform features:
- Automatic and semi-automatic monthly water quality and quantity mapping
- Time-series analytics and forecasting of eutrophication spread
- Downloadable raster outputs, web map views, and structured reports

## Key Concepts

A **project** represents a specific water body or region being monitored.

**Context layers** provide essential geospatial context such as administrative boundaries, land cover, or rainfall.

**Indicators** are derived from satellite indices like:
- AWEI (Automated Water Extraction Index)
- NDTI (Normalized Difference Turbidity Index)
- NDCI (Normalized Difference Chlorophyll Index)
- SABI (Surface Algal Bloom Index)


### Disclaimer

<div class="admonition warning">
This platform is intended for environmental monitoring and decision support. Users must independently verify all information before acting. SANSA and contributors are not liable for any adverse outcomes resulting from use of the platform.
</div>

### Purpose

To support evidence-based decisions around water resources through automated monitoring tools and EO-based analytics.

### Scope of Project

- Monthly index computation (AWEI, NDTI, NDCI, SABI)
- Integration of in-situ and satellite data
- API access to analysis results
- Report generation in PDF and TIFF formats
- Dockerized deployment with cloud support

### Project Roadmap

![Project Roadmap](img/roadmap.png)  
[Roadmap Document](roadmap/2025-timeline.md)

#### Contributing

We welcome collaboration! Check our [contributor guidelines](about/contributing.md) to get started.

#### Code of Conduct

See our [Code of Conduct](about/code-of-conduct.md) for participation standards.

#### Diversity Statement

No matter how you identify yourself or how others perceive you: we welcome you.
We welcome contributions from everyone as long as they interact constructively
with our community.

## Project Partners

![SANSA](img/sansa-logo.png)
[SANSA](https://www.sansa.org.za) – Project owner

<!-- Add more partner logos/links as needed -->

#### Releases

[GitHub Releases](https://github.com/kartoza/SANSA-Water-Quality-and-Quantity/releases)

#### Contributor License Agreement (CLA)

By contributing, you agree to our [Contributor License Agreement](about/contributing.md).

#### License

Licensed under the GNU Affero General Public License v3.0.  
[License details](about/license.md)

![Kartoza Logo](img/KartozaLogo-320x132.png)
