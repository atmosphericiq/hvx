# HVX: High-Voltage AC Induction and Simulation Toolkit

Welcome to HVX, the cutting-edge open-source library revolutionizing high-voltage AC induction simulations. Designed with geospatial engineers and electrical simulation experts in mind, HVX combines unparalleled precision with unmatched performance. Get ready to explore the power of spatial data processing, line segmentation, and high-voltage simulation—all in one robust package.

## 🚀 Features

- **Advanced Line Processing**: Master spatial data with innovative line segmentation and vector handling.
- **High-Voltage Simulations**: Employ comprehensive simulation tools built on `PySpice`.
- **GIS Toolkit Integration**: Leverages the [GIS Toolkit](https://github.com/atmosphericiq/gis-toolkit) for powerful geospatial data processing capabilities.
- **Open GIS Integration**: Seamlessly integrates with `osgeo`'s powerful OGR and OSR libraries.
- **Effortless Parallel Processing**: Boost performance using advanced parallel computation techniques.
- **Complete Testing Suite**: Ensure code reliability with extensive unit tests.

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

Join our vibrant community of contributors and help further enhance HVX! Fork, clone, and start your journey by contributing through pull requests. We value collaboration, creativity, and, above all, a spirit of growth.

## 🎫 License

HVX is open source and licensed under the MIT License—perfect for community growth and development.

## 🌐 Connect with Us

Engage with a community of innovators and simulation enthusiasts. Share ideas, exchange knowledge, and receive support through our dedicated chat channels and forums.

Let's redefine what's possible in high-voltage simulations.