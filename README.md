# QGIS-Intersection-Point-Generator

This project is a QGIS plugin designed to generate intersection points between line and polygon shapefiles. Using the RTree spatial indexing and the QGIS API, it efficiently identifies and processes geometries, providing unmatched and matched features as separate outputs.

## Features

    •    Interactive Shapefile Selection: Allows users to select line and polygon shapefiles interactively.
    •    Intersection Point Generation: Detects intersection points between lines and polygons.
    •    Unmatched Features Layers: Separates unmatched lines and polygons into their respective layers for further analysis.
    •    Optimized with RTree: Uses spatial indexing to speed up geometric computations.
    •    Seamless QGIS Integration: Adds the generated layers to the QGIS project automatically.
    
## Scientific Background

Geospatial analysis often involves detecting relationships between different geometric features. This plugin leverages RTree spatial indexing for optimized intersection detection, combined with QGIS API for processing and visualizing large datasets. The robust design enables applications in urban planning, network analysis, and environmental studies.

## Requirements

To run the plugin, you need:
    •    QGIS 3.x installed.
    •    Python Libraries:
        •    rtree
        
## Usage

    1.    Clone the repository:
        git clone git@github.com:aktercan/Intersection-Point-Generator.git 
        cd Intersection-Point-Generator

    2.    Place the plugin folder in your QGIS plugin directory:
        •    Linux/macOS: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
        •    Windows: %AppData%\QGIS\QGIS3\profiles\default\python\plugins\
    
    3.    Restart QGIS and enable the plugin from the Plugin Manager.
    
    4.    Use the toolbar icon or menu entry to activate the plugin:
        •    Select the line and polygon shapefiles interactively.
        •    Review the generated intersection points and unmatched features in the QGIS project.

## Example Output

    •    Intersection Points: New point layer showing intersections.
    •    Unmatched Lines: Line features with no intersections.
    •    Unmatched Polygons: Polygon features with no intersections.

## Limitations and Future Improvements

    •    Large Datasets: Performance may degrade with extremely large datasets.
    •    Advanced Intersection Logic: Future versions could include buffer-based or proximity-based intersection detection.
    •    GUI Enhancements: Add an advanced GUI for feature filtering and analysis.
    

