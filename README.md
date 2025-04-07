# HVX: High-Voltage AC Induction and Simulation Toolkit

Welcome to HVX, the cutting-edge open-source library revolutionizing high-voltage AC induction simulations. Designed with geospatial engineers and electrical simulation experts in mind, HVX combines unparalleled precision with unmatched performance. Get ready to explore the power of spatial data processing, line segmentation, and high-voltage simulation—all in one robust package.

## 🚀 Features

- **Advanced Line Processing**: Master spatial data with innovative line segmentation and vector handling.
- **High-Voltage Simulations**: Employ comprehensive simulation tools built on `PySpice`.
- **GIS Toolkit Integration**: Leverages the [GIS Toolkit](https://github.com/atmosphericiq/gis-toolkit) for powerful geospatial data processing capabilities.
- **Open GIS Integration**: Seamlessly integrates with `osgeo`'s powerful OGR and OSR libraries.
- **Effortless Parallel Processing**: Boost performance using advanced parallel computation techniques.
- **Complete Testing Suite**: Ensure code reliability with extensive unit tests.

# Project Roadmap

The project is currently in the early stages of development, focusing on geospatial processing and electrical simulation using Python. This section outlines the expected progression of the project throughout 2025.

## Current State

- **Focus on Fields.py**: The existing project revolves around geospatial analysis and processing lines with specific interest in voltage distribution and magnetic fields.
- Utilizes core Python libraries such as `numpy`, `osgeo.ogr`, and `PySpice`.
- Includes fundamental components for geospatial data manipulation and electrical simulation with components like `MetalPipelineTransmissionSegment` and `PipelineNetwork`.

## Future Direction

As we progress through 2025, the project will expand towards a more comprehensive simulation using SPICE (Simulation Program with Integrated Circuit Emphasis):

- **Q2 2025**: Begin Integrating More Complex SPICE Components
  - Develop advanced simulation components using `PySpice`.
  - Enhance transmission line models with more detailed attributes and configurations.
  - Incorporate varying substrates and coatings with specific physical properties.

- **Q3 2025**: Expand the Mathematical Framework
  - Refine the mathematical models associated with geospatial and electrical properties.
  - Broaden the testing framework to ensure accuracy and reliability.
  - Integrate additional geospatial layers with different types of data (e.g., resistivity, soil type).


## 🎉 Usage

### Getting Started in Seconds

Run the HVX library from within a Docker container for isolation and consistent performance:

1. **Build the Docker Image**:

    ```bash
    docker build -t hvx-toolkit .
    ```

2. **Run the Docker Container**:

    ```bash
    docker run --rm -it hvx-toolkit /bin/bash
    ```

3. **Execute the Main Script**:

    Inside the Docker container, run the main field processing script with:

    ```bash
    python3 fields.py --continuity-shapefile path/to/shapefile \
                      --output-shapefile path/to/output \
                      --parallelism 4 \
                      --base-height 10 \
                      --powerline-file path/to/powerline \
                      --resistivity-file path/to/resistivity \
                      --resistivity-field-name FieldName \
                      --decouplers-gpkg path/to/decouplers \
                      --annual-survey-gpkg path/to/survey
    ```

## 🔧 Installation

Ensure that Docker is installed on your system to leverage the capabilities of the containerized environment efficiently.

The HVX project depends on the [GIS Toolkit](https://github.com/atmosphericiq/gis-toolkit), which enhances the geospatial data processing capabilities essential for advanced simulations and accurate spatial analysis.

## 🤝 Contributing

HVX is mostly maintained by me, [haydenth](https://github.com/haydenth), and we're on the lookout for more contributors who are willing to help.

If you have an idea or find a bug, feel free to fork the project, make your changes, and submit a pull request. We appreciate any contributions, large or small, and believe they all help our community grow.

## 🎫 License

HVX is open source and licensed under the MIT License—perfect for community growth and development.

## 🌐 Connect with Us

Engage with a community of innovators and simulation enthusiasts. Share ideas, exchange knowledge, and receive support through our dedicated chat channels and forums.

Let's redefine what's possible in high-voltage simulations.
