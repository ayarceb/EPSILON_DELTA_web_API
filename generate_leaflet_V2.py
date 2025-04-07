import math

def generate_leaflet_html(filename="leaflet_hpc_refined.html"):
    """
    We fit a power-law cost factor(N) = a*N^b using two references:
      1) 'Large domain at 10 km' => 2.72e6 cells => 1.47e-6 CPU-hrs/cell/day
      2) 'Medellin at 1 km'     => 1.0e6 cells   => 2.4e-5  CPU-hrs/cell/day

    Then HPC for 1 day => N * costFactor(N).
    We'll let the user choose bounding box and resolution, then compute N.
    """

    # --- 1) Fit power law from the two references
    N1 = 2.72e6
    cf1 = 1.47e-6   # CPU-hrs/cell/day
    N2 = 1.0e6
    cf2 = 2.4e-5    # CPU-hrs/cell/day

    lnN1 = math.log(N1)
    lnCF1 = math.log(cf1)
    lnN2 = math.log(N2)
    lnCF2 = math.log(cf2)

    b = (lnCF2 - lnCF1) / (lnN2 - lnN1)
    a = math.exp(lnCF1 - b*lnN1)

    # We'll embed these into the HTML/JS.
    # (We want them as text so the browser can do the exponent.)
    a_str = f"{a:.9g}"
    b_str = f"{b:.9g}"

    # The HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <title>Refined HPC Estimate (Two References)</title>
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
      width: 70px;
    }}
    #info {{
      margin: 5px 0;
      font-weight: bold;
    }}
    #info-details {{
      color: #555;
      font-size: 0.9em;
    }}
    .highlight {{
      color: #0055cc;
    }}
  </style>
</head>
<body>

<div id="controls">
  <label class="label-input">
    North:
    <input id="input-north" type="text" value="7.0">
  </label>
  <label class="label-input">
    South:
    <input id="input-south" type="text" value="6.0">
  </label>
  <label class="label-input">
    West:
    <input id="input-west" type="text" value="-76.0">
  </label>
  <label class="label-input">
    East:
    <input id="input-east" type="text" value="-75.0">
  </label>
  <br><br>
  <label class="label-input">
    Resolution (deg):
    <input id="input-res" type="text" value="0.001">
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
  // We'll store a, b from Python
  const a = {a_str};
  const b = {b_str};

  // We'll parse user inputs, compute HPC usage
  function computeHPC() {{
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
    ) {{
      alert('Please enter valid numeric coordinates, resolution, days, and cores (>0).');
      return null;
    }}

    // # of cells in bounding box
    let deltaLat = Math.abs(north - south);
    let deltaLon = Math.abs(east - west);

    let nLat = Math.floor(deltaLat / resDeg);
    let nLon = Math.floor(deltaLon / resDeg);
    let totalCells = nLat * nLon;

    // costFactor(N) = a * N^b
    // HPC for 1 day = totalCells * costFactor(N)
    // HPC for 'days' => times days
    // Then wall time = HPC / cores

    let costFactorN = a * Math.pow(totalCells, b);
    let cpuHours_1day = totalCells * costFactorN;
    let cpuHours_total = cpuHours_1day * days;
    let wallTime_hrs = cpuHours_total / cores;

    // Convert to HH:MM
    let totalMin = Math.floor(wallTime_hrs * 60);
    let hh = Math.floor(totalMin / 60);
    let mm = totalMin % 60;

    return {{
      totalCells,
      costFactorN,
      cpuHours_total,
      days,
      cores,
      wallTime_hrs,
      hh,
      mm
    }};
  }}

  // Create the Leaflet map
  var map = L.map('map').setView([6.5, -75.5], 8); // near Medellín
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  // We'll keep track of the bounding box layer
  let boundingBoxLayer = null;

  function drawAndCalculate() {{
    let data = computeHPC();
    if(!data) return;

    let north = parseFloat(document.getElementById('input-north').value);
    let south = parseFloat(document.getElementById('input-south').value);
    let west = parseFloat(document.getElementById('input-west').value);
    let east = parseFloat(document.getElementById('input-east').value);

    // Draw bounding box
    if(boundingBoxLayer) {{
      map.removeLayer(boundingBoxLayer);
    }}
    let bounds = [[south, west], [north, east]];
    boundingBoxLayer = L.rectangle(bounds, {{
      color: 'red',
      weight: 2,
      fill: false
    }}).addTo(map);

    // Fit map
    map.fitBounds(bounds);

    let infoDiv = document.getElementById('info');
    let infoDetails = document.getElementById('info-details');

    let c = data;

    infoDiv.innerHTML = 
      'Cells: ' + c.totalCells.toLocaleString() + 
      ', HPC cost factor(N) = ' + c.costFactorN.toExponential(2) + ' CPU-hrs/cell/day' +
      '<br>Total CPU-hrs (for ' + c.days + ' day(s)): ' + c.cpuHours_total.toFixed(2);

    infoDetails.innerHTML =
      '<span class="highlight">Estimated wall time on ' + c.cores + 
      ' cores:</span> ' + c.hh + 'h ' + c.mm + 'm';
  }}

  // Hook up the button
  document.getElementById('draw-btn').addEventListener('click', drawAndCalculate);

  // Do an initial run
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
