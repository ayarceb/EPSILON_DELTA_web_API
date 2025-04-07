def generate_leaflet_html(filename="leaflet_hpc_compare.html"):
    """
    Compare approximate HPC usage/time for a chosen bounding box
    at both 10 km and 1 km resolution, anchored to the same reference domain.

    Reference: 
      - Domain ~2.72e6 cells at 10 km resolution (for Colombia).
      - 8 cores, 30 minutes = 0.5 hours => 4 CPU-hrs total for 1 day.
      => HPC factor (10 km) = 4 / 2.72e6 = ~1.47e-6 CPU-hrs/cell/day.
      => HPC factor (1 km) ~ 1.47e-6 * 10,000 = 1.47e-2 CPU-hrs/cell/day 
         (since 1 km has 100×100 more cells than 10 km for the same lat-lon box).
    """

    # HPC cost at 10 km resolution, from the reference
    cost_factor_10km = 4.0 / 2_720_000  # ~1.47e-6 CPU-hrs/cell/day
    # HPC cost at 1 km resolution is 10,000× larger (2D scaling)
    cost_factor_1km = cost_factor_10km * 10_000

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>Draw Bounding Box & HPC Compare (10 km vs. 1 km)</title>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      width: 100%;
      font-family: sans-serif;
    }}
    #controls {{
      padding: 10px;
      background: #f2f2f2;
    }}
    #map {{
      height: calc(100% - 210px);
      width: 100%;
    }}
    .label-input {{
      margin-right: 15px;
    }}
    input {{
      width: 80px;
    }}
    #info-10km, #info-1km {{
      margin: 5px 0;
      font-weight: bold;
    }}
    #info-10km {{
      color: #333;
    }}
    #info-1km {{
      color: #0077cc; /* Just a different color for clarity */
    }}
  </style>
</head>
<body>

<div id="controls">
  <label class="label-input">
    North:
    <input id="input-north" type="text" value="13.0">
  </label>
  <label class="label-input">
    South:
    <input id="input-south" type="text" value="-4.0">
  </label>
  <label class="label-input">
    West:
    <input id="input-west" type="text" value="-82.0">
  </label>
  <label class="label-input">
    East:
    <input id="input-east" type="text" value="-66.0">
  </label>
  <br><br>
  <label class="label-input">
    Days to Simulate:
    <input id="input-days" type="text" value="1">
  </label>
  <label class="label-input">
    # of CPU cores:
    <input id="input-cores" type="text" value="8">
  </label>
  <button id="draw-btn">Draw & Calculate</button>

  <div id="info-10km"></div>
  <div id="info-1km"></div>
</div>

<div id="map"></div>

<script>
  // Start map near Colombia as an example
  var map = L.map('map').setView([5, -74], 5);

  // Add basemap
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  // We'll track bounding box so we can remove it before drawing a new one
  var boundingBoxLayer = null;

  // 10 km resolution -> about 0.01 degrees
  var resolutionDeg_10km = 0.01;
  // 1 km resolution -> about 0.001 degrees
  var resolutionDeg_1km = 0.001;

  // HPC cost factors (CPU-hrs/cell/day), from our Python constants
  var costFactor_10km = {cost_factor_10km};
  var costFactor_1km = {cost_factor_1km};

  function drawAndCalculate() {{
    var north = parseFloat(document.getElementById('input-north').value);
    var south = parseFloat(document.getElementById('input-south').value);
    var west = parseFloat(document.getElementById('input-west').value);
    var east = parseFloat(document.getElementById('input-east').value);

    var days = parseFloat(document.getElementById('input-days').value);
    var cores = parseFloat(document.getElementById('input-cores').value);

    if (
      isNaN(north) || isNaN(south) || isNaN(west) || isNaN(east)
      || isNaN(days) || isNaN(cores) || days <= 0 || cores <= 0
    ) {{
      alert('Please enter valid numeric coordinates, days, and cores (all > 0).');
      return;
    }}

    // Remove old bounding box if it exists
    if (boundingBoxLayer) {{
      map.removeLayer(boundingBoxLayer);
    }}

    // Create bounding box
    var bounds = [[south, west], [north, east]];
    boundingBoxLayer = L.rectangle(bounds, {{
      color: 'red',
      weight: 2,
      fill: false
    }}).addTo(map);

    // Zoom map to the bounding box
    map.fitBounds(bounds);

    //--- 10 km domain size
    var deltaLat = Math.abs(north - south);
    var deltaLon = Math.abs(east - west);

    var squaresLat_10km = Math.floor(deltaLat / resolutionDeg_10km);
    var squaresLon_10km = Math.floor(deltaLon / resolutionDeg_10km);
    var totalCells_10km = squaresLat_10km * squaresLon_10km;

    // HPC cost for 10 km, 1 day
    var totalCPUHours_10km_1day = totalCells_10km * costFactor_10km;
    // HPC cost for 'days' days
    var totalCPUHours_10km = totalCPUHours_10km_1day * days;
    // Wall-clock time for 10 km
    var totalWallTimeHours_10km = totalCPUHours_10km / cores;
    var totalWallTimeMin_10km = Math.floor(totalWallTimeHours_10km * 60);
    var hh_10km = Math.floor(totalWallTimeMin_10km / 60);
    var mm_10km = totalWallTimeMin_10km % 60;

    //--- 1 km domain size
    var squaresLat_1km = Math.floor(deltaLat / resolutionDeg_1km);
    var squaresLon_1km = Math.floor(deltaLon / resolutionDeg_1km);
    var totalCells_1km = squaresLat_1km * squaresLon_1km;

    // HPC cost for 1 km, 1 day
    var totalCPUHours_1km_1day = totalCells_1km * costFactor_1km;
    // HPC cost for 'days' days
    var totalCPUHours_1km = totalCPUHours_1km_1day * days;
    // Wall-clock time for 1 km
    var totalWallTimeHours_1km = totalCPUHours_1km / cores;
    var totalWallTimeMin_1km = Math.floor(totalWallTimeHours_1km * 60);
    var hh_1km = Math.floor(totalWallTimeMin_1km / 60);
    var mm_1km = totalWallTimeMin_1km % 60;

    //--- Display
    var info10 = document.getElementById('info-10km');
    var info1 = document.getElementById('info-1km');

    info10.innerHTML = 
      '[10 km] ' +
      'Grid: ' + squaresLat_10km + ' × ' + squaresLon_10km + ' = ' + totalCells_10km + ' cells. ' +
      'CPU-hrs: ' + totalCPUHours_10km.toFixed(2) + ' (for ' + days + ' day(s)). ' +
      'Wall time on ' + cores + ' core(s): ' + hh_10km + ' hr ' + mm_10km + ' min.';

    info1.innerHTML = 
      '[1 km] ' +
      'Grid: ' + squaresLat_1km + ' × ' + squaresLon_1km + ' = ' + totalCells_1km + ' cells. ' +
      'CPU-hrs: ' + totalCPUHours_1km.toFixed(2) + ' (for ' + days + ' day(s)). ' +
      'Wall time on ' + cores + ' core(s): ' + hh_1km + ' hr ' + mm_1km + ' min.';
  }}

  // Click event
  document.getElementById('draw-btn').addEventListener('click', drawAndCalculate);

  // Initial draw
  drawAndCalculate();
</script>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML file generated: {filename}")
    print("Open this file in your browser to test it.")

if __name__ == "__main__":
    generate_leaflet_html()
