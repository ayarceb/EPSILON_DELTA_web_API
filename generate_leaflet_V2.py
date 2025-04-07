def generate_leaflet_html(filename="simple_piecewise_hpc.html"):
    """
    Generates an HTML page that uses a *very simplified* piecewise + linear
    interpolation between two known HPC reference points:
      1) Big domain (2.72e6 cells) => 4 CPU-hrs/day
      2) Small domain (1.0e6 cells) => 24 CPU-hrs/day

    HPC_1day(N):
      If N <= 1e6:
          HPC_1day(N) = 24 * (N / 1e6)
      If N >= 2.72e6:
          HPC_1day(N) = 4 * (N / 2.72e6)
      If 1e6 < N < 2.72e6:
          linear interpolation from (1e6 => 24) to (2.72e6 => 4)
    Then HPC_total = HPC_1day(N) * (days)
    Wall time = HPC_total / (cores)

    VERY approximate, but ensures smaller domain doesn't exceed big domain time.
    """

    html_content = r"""<!DOCTYPE html>
<html>
<head>
  <title>Simple Piecewise HPC Estimate</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    html, body {
      margin: 0; padding: 0;
      width: 100%; height: 100%;
      font-family: sans-serif;
    }
    #controls {
      background: #f2f2f2;
      padding: 10px;
    }
    .label-input {
      margin-right: 10px;
    }
    #map {
      width: 100%;
      height: calc(100% - 170px);
    }
    #info {
      margin: 5px 0;
      font-weight: bold;
    }
    #info-details {
      color: #555;
      font-size: 0.9em;
    }
  </style>
</head>
<body>

<div id="controls">
  <label class="label-input">
    North:
    <input id="input-north" type="text" value="7">
  </label>
  <label class="label-input">
    South:
    <input id="input-south" type="text" value="6">
  </label>
  <label class="label-input">
    West:
    <input id="input-west" type="text" value="-76">
  </label>
  <label class="label-input">
    East:
    <input id="input-east" type="text" value="-75">
  </label>
  <br><br>
  <label class="label-input">
    Resolution (deg):
    <input id="input-res" type="text" value="0.01">
  </label>
  <label class="label-input">
    Days:
    <input id="input-days" type="text" value="1">
  </label>
  <label class="label-input">
    Cores:
    <input id="input-cores" type="text" value="8">
  </label>
  <button id="draw-btn">Draw & Calculate</button>
  
  <div id="info"></div>
  <div id="info-details"></div>
</div>

<div id="map"></div>

<script>
  // We'll implement the piecewise HPC logic in JavaScript.

  function piecewiseHPC_1day(N) {
    // N = total number of cells
    // 1) If N <= 1e6: HPC_1day(N) = 24 * (N / 1e6)
    if (N <= 1e6) {
      return 24.0 * (N / 1.0e6);
    }
    // 2) If N >= 2.72e6: HPC_1day(N) = 4 * (N / 2.72e6)
    else if (N >= 2.72e6) {
      return 4.0 * (N / 2.72e6);
    }
    // 3) If in between, linear interpolation from (1e6 => 24) to (2.72e6 => 4)
    else {
      let x1 = 1.0e6;    // domain size #1
      let y1 = 24.0;     // HPC at #1
      let x2 = 2.72e6;   // domain size #2
      let y2 = 4.0;      // HPC at #2

      // fraction between x1 and x2
      let frac = (N - x1) / (x2 - x1);
      return y1 + (y2 - y1)*frac;
    }
  }

  // Leaflet map init
  var map = L.map('map').setView([6.5, -75.5], 8); // near Medellín
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  let boundingBoxLayer = null;

  function drawAndCalculate() {
    let north = parseFloat(document.getElementById('input-north').value);
    let south = parseFloat(document.getElementById('input-south').value);
    let west = parseFloat(document.getElementById('input-west').value);
    let east = parseFloat(document.getElementById('input-east').value);
    let resDeg = parseFloat(document.getElementById('input-res').value);

    let days = parseFloat(document.getElementById('input-days').value);
    let cores = parseFloat(document.getElementById('input-cores').value);

    if (
      isNaN(north) || isNaN(south) || isNaN(west) || isNaN(east) ||
      isNaN(resDeg) || isNaN(days) || isNaN(cores) ||
      days <= 0 || cores <= 0 || resDeg <= 0
    ) {
      alert("Enter valid positive numeric values!");
      return;
    }

    // Compute bounding box cells:
    let dLat = Math.abs(north - south);
    let dLon = Math.abs(east - west);

    let nLat = Math.floor(dLat / resDeg);
    let nLon = Math.floor(dLon / resDeg);
    let totalCells = nLat * nLon;

    // HPC for 1 day in CPU-hrs
    let hpc_1day = piecewiseHPC_1day(totalCells);

    // HPC for all days
    let hpc_total = hpc_1day * days;

    // wall-clock hours
    let wall_hours = hpc_total / cores;
    let wall_minutes_total = Math.floor(wall_hours * 60);
    let hh = Math.floor(wall_minutes_total / 60);
    let mm = wall_minutes_total % 60;

    // Draw bounding box
    if (boundingBoxLayer) {
      map.removeLayer(boundingBoxLayer);
    }
    let bounds = [[south, west], [north, east]];
    boundingBoxLayer = L.rectangle(bounds, {
      color: 'red',
      weight: 2,
      fill: false
    }).addTo(map);
    map.fitBounds(bounds);

    // Display info
    let infoDiv = document.getElementById("info");
    let detailsDiv = document.getElementById("info-details");

    infoDiv.innerHTML = 
      "Grid size: " + nLat + " × " + nLon +
      " = " + totalCells.toLocaleString() + " cells.<br>" +
      "HPC for 1 day: " + hpc_1day.toFixed(2) + " CPU-hrs.";

    detailsDiv.innerHTML =
      "Total HPC for " + days + " day(s): " + hpc_total.toFixed(2) + 
      " CPU-hrs. <br>" +
      "Wall time on " + cores + " cores: " + hh + " hr " + mm + " min.";
  }

  document.getElementById("draw-btn").addEventListener("click", drawAndCalculate);

  // Initial run
  drawAndCalculate();
</script>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML file generated: {filename}\nOpen it in your browser to test it!")

if __name__ == "__main__":
    generate_leaflet_html()
