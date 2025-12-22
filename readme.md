# **NYC Real-Time Transportation Dashboard**

This is a high-performance real-time transportation visualization dashboard built with [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/). It is designed to provide real-time monitoring and data visualization for the New York City (NYC) public transportation system. My deployed website link is https://gtfs-dashboard333-wnplbr5nrucypzg9dsi8ac.streamlit.app/.

The project integrates real-time data feeds from the MTA (Subway, Bus, LIRR, MNR) and Citibike status, optimized for performance and user experience.

## **✨ Key Features**

* **Multi-Modal Transportation Support**:  
  * 🚇 **NYC Subway**: Supports all lines, utilizing official MTA colors.  
  * 🚌 **Bus**: Loads by borough (Bronx, Brooklyn, Manhattan, Queens, SI) to optimize rendering, with support for collapsing and filtering.  
  * 🚆 **Commuter Rail**: Supports LIRR (Long Island Rail Road) and MNR (Metro-North Railroad).  
  * 🚲 **Citibike**: Real-time display of available bikes/docks, dynamically colored based on availability.  
* **Smart Dynamic Topology**:  
  * **Filter Inactive Stops**: When "Show next-arrival time" is checked, the map automatically hides stops with no current scheduled service and reconnects the route geometry, visualizing the actual operational topology.  
  * **Real-Time Arrival Predictions**: Hover to see the estimated arrival time of the next train (Timezone issues fixed).  
* **High-Performance Architecture**:  
  * **Lazy Loading**: Static GTFS data is loaded on demand and cached, significantly reducing memory usage.  
  * **Auto-Refresh**: Integrated with streamlit-autorefresh for non-blocking data updates every 30 seconds.  
* **UI/UX Optimization**:  
  * **Full-Screen Mode**: Optimized CSS removes excess whitespace to maximize the map display area.  
  * **Official Branding**: Built-in official MTA brand color codes ensure visual accuracy.

## **📦 Installation**

This project is built with Python. Please ensure your environment meets the following requirements.

### **1\. Create Environment and Install Dependencies**

Python 3.9+ is recommended.

Create a requirements.txt file with the following content:

pandas\>=1.3.5  
geopandas  
osmnx==1.1.1  
dash  
dash-bootstrap-components  
plotly  
gtfs-realtime-bindings  
streamlit  
protobuf  
streamlit-autorefresh

Run the installation command:

pip install \-r requirements.txt

**Note**: Although the dependency list includes dash related libraries, the main entry point app\_streamlit.py is a pure Streamlit application. If you do not need to run legacy Dash modules within the project, you may try omitting the Dash dependencies.

## **📂 Data Preparation (GTFS)**

The project requires static GTFS data to run. Please create a GTFS folder in the project root directory and place the unzipped MTA GTFS data (containing routes.txt, stops.txt, stop\_times.txt, trips.txt, etc.) according to the structure below:

Project Root  
├── app\_streamlit.py  
├── utils\_streamlit.py  \<-- Ensure this utility file exists  
├── GTFS/               \<-- Static Data Directory  
│   ├── subway/  
│   ├── bus\_bronx/  
│   ├── bus\_brooklyn/  
│   ├── bus\_manhattan/  
│   ├── bus\_queens/  
│   ├── bus\_staten\_island/  
│   ├── bus\_new\_jersy/  
│   ├── LIRR/  
│   └── MNR/  
└── requirements.txt

## **🚀 Running the App**

In the project root directory, launch the application using Streamlit:

streamlit run app\_streamlit.py

Once started, your browser should automatically open http://localhost:8501.

## **⚙️ Configuration & Usage**

### **Sidebar Options**

1. **Layer**: Switch between Subway, LIRR, Bus, or Citibike maps.  
2. **Bus borough**: Appears only when "Bus" is selected; use this to switch boroughs to reduce rendering load.  
3. **Rendering options**:  
   * Show next-arrival time: **Core Feature**. Checking this triggers API requests, filters out stops with no service, and displays real-time data.  
   * Show stop markers: Displays circular markers for stops on the map (may impact performance with large datasets).  
4. **Auto refresh**: Toggles the 30-second automatic data refresh.

### **Troubleshooting**

* **Map shows no routes**: Please check if the CSV files in the GTFS folder are complete and the paths are correct.  
* **Real-time data errors**: Please check your internet connection or verify if the API Key in utils\_streamlit.py is valid (as this project relies on the MTA API).

## 

