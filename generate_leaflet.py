def generate_leaflet_html(filename="leaflet_hpc_estimate_10km.html"):
    """
    This script derives the HPC usage from a reference simulation:
    - 10 km resolution domain over Colombia (~2.72 million cells).
    - 8 cores, 30 minutes for 1 day => 4 CPU-hrs/day total.
    => HPC factor = 4 / 2.72e6 = ~1.47e-6 CPU-hrs/cell/day.
    """

    # Corrected HPC cost factor for 10 km resolution
    cost_factor = 4 / 2_720_000  # ~1.47e-6 CPU-hrs/cell/day

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>Draw Bounding Box & HPC Estimate (10 km)</title>
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
      height: calc(100% - 180px);
      width: 100%;
    }}
    .label-input {{
      margin-right: 15px;
    }}
    input {{
      width: 80px;
    }}
    #info {{
      margin: 5px 0;
      font-weight: bold;
      color: #333;
    }}
    #info-hpc {{
      margin: 5px 0;
      font-weight: normal;
      color: #666;
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

  <div id="info"></div>
  <div id="info-hpc"></div>
</div>

<div id="map"></div>

<script>
  // Create the map centered near Colombia as an example
  var map = L.map('map').setView([5, -74], 5);

  // Add a basemap layer
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  // We'll track our bounding box so we can remove it before drawing a new one
  var boundingBoxLayer = null;

  // For 10 km resolution, about 0.01 degrees
  var resolutionDeg = 0.01;

  // HPC cost factor (CPU-hours per cell per day),
  // derived from reference 10 km run
  var costFactor = {cost_factor};

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

    // Create the bounding box as a Leaflet rectangle
    var bounds = [[south, west], [north, east]];
    boundingBoxLayer = L.rectangle(bounds, {{
      color: 'red',
      weight: 2,
      fill: false
    }}).addTo(map);

    // Zoom the map to this bounding box
    map.fitBounds(bounds);

    // Calculate how many squares of ~10 km (0.01 deg) in each dimension
    var deltaLat = Math.abs(north - south);
    var deltaLon = Math.abs(east - west);

    var squaresLat = Math.floor(deltaLat / resolutionDeg);
    var squaresLon = Math.floor(deltaLon / resolutionDeg);
    var totalCells = squaresLat * squaresLon;

    // HPC cost for 1 day
    var totalCPUHours_1day = totalCells * costFactor;
    // HPC cost for 'days' days
    var totalCPUHours = totalCPUHours_1day * days;

    // Wall-clock time if using 'cores'
    var totalWallTimeHours = totalCPUHours / cores;
    var totalWallTimeMinutes = Math.floor(totalWallTimeHours * 60);
    var hh = Math.floor(totalWallTimeMinutes / 60);
    var mm = totalWallTimeMinutes % 60;

    // Show info to user
    var infoDiv = document.getElementById('info');
    infoDiv.innerHTML = 
      'Grid size: ' + squaresLat + ' × ' + squaresLon +
      ' = ' + totalCells + ' cells (at ~10 km).';

    var infoHPCDiv = document.getElementById('info-hpc');
    infoHPCDiv.innerHTML = 
      'Estimated HPC usage: ' + totalCPUHours.toFixed(2) + ' CPU-hrs total ' +
      '(for ' + days + ' day(s)).<br>' +
      'Estimated wall-clock time on ' + cores + ' core(s): ' +
      hh + ' hr ' + mm + ' min.';
  }}

  // Listen for the button click
  document.getElementById('draw-btn').addEventListener('click', drawAndCalculate);

  // Calculate on page load
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
