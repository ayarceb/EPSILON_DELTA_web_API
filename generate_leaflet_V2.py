def generate_leaflet_draw_hpc_html(filename="leaflet_draw_hpc.html"):
    """
    Combines:
      1) Leaflet.Draw for drawing or editing a single rectangle on the map.
      2) Text inputs for North, South, West, East, resolution, days, cores.
      3) A piecewise HPC approximation (as we used before) to estimate CPU-hrs
         and wall-clock time based on domain size.

    Usage:
      - Draw or move the rectangle on the map, then click "Rectangle → Inputs"
        to see the numeric bounding box.
      - Or type the bounding box corners manually and click "Inputs → Rectangle".
      - Set resolution (deg), #days, and #cores. Then click "Calculate HPC" to
        see HPC hours and approximate wall time.
    """

    html_content = r"""<!DOCTYPE html>
<html>
<head>
  <title>Leaflet Draw + HPC Approx</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Leaflet CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <!-- Leaflet Draw CSS & JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
  <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>

  <style>
    html, body {
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      font-family: sans-serif;
    }
    #controls {
      background: #f2f2f2;
      padding: 10px;
    }
    .label-input {
      margin-right: 10px;
    }
    input {
      width: 70px;
    }
    #map {
      width: 100%;
      height: calc(100% - 210px);
    }
    #info, #info-hpc {
      margin: 5px 0;
      font-weight: bold;
    }
    #info-hpc {
      color: #555;
      font-size: 0.9em;
    }
  </style>
</head>
<body>

<div id="controls">
  <!-- BOUNDING BOX INPUTS -->
  <label class="label-input">North: 
    <input id="input-north" type="text" value="24.0"/>
  </label>
  <label class="label-input">South:
    <input id="input-south" type="text" value="23.0"/>
  </label>
  <label class="label-input">West:
    <input id="input-west"  type="text" value="-103.0"/>
  </label>
  <label class="label-input">East:
    <input id="input-east"  type="text" value="-102.0"/>
  </label>
  <button id="btn-rect-to-inputs">Rectangle → Inputs</button>
  <button id="btn-inputs-to-rect">Inputs → Rectangle</button>
  <br><br>

  <!-- HPC INPUTS -->
  <label class="label-input">Resolution (deg):
    <input id="input-res" type="text" value="0.01"/>
  </label>
  <label class="label-input">Days:
    <input id="input-days" type="text" value="1"/>
  </label>
  <label class="label-input">Cores:
    <input id="input-cores" type="text" value="8"/>
  </label>
  <button id="btn-calc-hpc">Calculate HPC</button>

  <div id="info"></div>
  <div id="info-hpc"></div>
</div>

<div id="map"></div>

<script>
  /////////////////////////////////
  // 1) MAP + LEAFLET.DRAW SETUP //
  /////////////////////////////////
  var map = L.map('map').setView([23.5, -102.5], 6);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  // A LayerGroup to store the drawn rectangle
  var drawnItems = new L.FeatureGroup();
  map.addLayer(drawnItems);

  // Create draw control
  var drawControl = new L.Control.Draw({
    edit: {
      featureGroup: drawnItems,
      edit: true,
      remove: true
    },
    draw: {
      marker: false,
      polyline: false,
      circle: false,
      circlemarker: false,
      polygon: false,
      // Only rectangle
      rectangle: {
        shapeOptions: {
          color: 'red',
          weight: 2
        }
      }
    }
  });
  map.addControl(drawControl);

  var activeRectangle = null;

  // When a new rectangle is created
  map.on(L.Draw.Event.CREATED, function(e){
    if (activeRectangle) {
      drawnItems.removeLayer(activeRectangle);
      activeRectangle = null;
    }
    var layer = e.layer;
    drawnItems.addLayer(layer);
    activeRectangle = layer;
  });

  // When rectangle is edited
  map.on(L.Draw.Event.EDITED, function(e){
    e.layers.eachLayer(function(layer){
      activeRectangle = layer;
    });
  });

  // When rectangle is deleted
  map.on(L.Draw.Event.DELETED, function(e){
    e.layers.eachLayer(function(layer){
      if (layer === activeRectangle) {
        activeRectangle = null;
      }
    });
  });

  /////////////////////////////////
  // 2) RECTANGLE <-> INPUTS     //
  /////////////////////////////////

  // Button: Rectangle -> Inputs
  document.getElementById('btn-rect-to-inputs').addEventListener('click', function(){
    if(!activeRectangle) {
      alert("No rectangle drawn!");
      return;
    }
    var b = activeRectangle.getBounds();
    var south = b.getSouth();
    var west  = b.getWest();
    var north = b.getNorth();
    var east  = b.getEast();

    document.getElementById('input-north').value = north.toFixed(5);
    document.getElementById('input-south').value = south.toFixed(5);
    document.getElementById('input-west').value  = west.toFixed(5);
    document.getElementById('input-east').value  = east.toFixed(5);
  });

  // Button: Inputs -> Rectangle
  document.getElementById('btn-inputs-to-rect').addEventListener('click', function(){
    var north = parseFloat(document.getElementById('input-north').value);
    var south = parseFloat(document.getElementById('input-south').value);
    var west  = parseFloat(document.getElementById('input-west').value);
    var east  = parseFloat(document.getElementById('input-east').value);

    if(isNaN(north) || isNaN(south) || isNaN(west) || isNaN(east)) {
      alert("Please enter valid numeric coords!");
      return;
    }
    if(south > north) {
      alert("South can't be greater than North!");
      return;
    }
    if(west > east) {
      alert("West can't be greater than East!");
      return;
    }

    // Remove old rect if any
    if(activeRectangle) {
      drawnItems.removeLayer(activeRectangle);
      activeRectangle = null;
    }

    var bounds = [[south, west],[north, east]];
    activeRectangle = L.rectangle(bounds, {color:'red', weight:2});
    drawnItems.addLayer(activeRectangle);
    map.fitBounds(bounds);
  });


  /////////////////////////////////
  // 3) HPC CALCULATION (Piecewise)
  /////////////////////////////////

  function hpcForOneDay(N) {
    // N = # of cells
    // piecewise approach:
    //   if N <= 1e6: HPC_1day(N) = 24 * (N/1e6)
    //   if N >= 2.72e6: HPC_1day(N) = 4 * (N/2.72e6)
    //   else: linear from 24@1e6 to 4@2.72e6
    if (N <= 1.0e6) {
      return 24.0 * (N / 1.0e6);
    }
    else if (N >= 2.72e6) {
      return 4.0 * (N / 2.72e6);
    }
    else {
      // linear interpolation
      let x1 = 1.0e6, y1 = 24.0;
      let x2 = 2.72e6, y2 = 4.0;
      let frac = (N - x1) / (x2 - x1);
      return y1 + (y2 - y1)*frac;
    }
  }

  // Button: Calculate HPC
  document.getElementById('btn-calc-hpc').addEventListener('click', function(){
    var north = parseFloat(document.getElementById('input-north').value);
    var south = parseFloat(document.getElementById('input-south').value);
    var west  = parseFloat(document.getElementById('input-west').value);
    var east  = parseFloat(document.getElementById('input-east').value);

    var resDeg = parseFloat(document.getElementById('input-res').value);
    var days   = parseFloat(document.getElementById('input-days').value);
    var cores  = parseFloat(document.getElementById('input-cores').value);

    if(isNaN(north) || isNaN(south) || isNaN(west) || isNaN(east) ||
       isNaN(resDeg) || isNaN(days) || isNaN(cores) ||
       days <= 0 || cores <= 0 || resDeg <=0 ) {
      alert("Check your numeric inputs (all must be > 0)!");
      return;
    }

    let dLat = Math.abs(north - south);
    let dLon = Math.abs(east - west);

    // # cells
    let nLat = Math.floor(dLat / resDeg);
    let nLon = Math.floor(dLon / resDeg);
    let totalCells = nLat * nLon;

    // HPC for 1 day
    let hpc_1day = hpcForOneDay(totalCells);

    // HPC total
    let hpc_total = hpc_1day * days;

    // wall clock
    let wall_hrs = hpc_total / cores;
    let total_min = Math.floor(wall_hrs * 60);
    let hh = Math.floor(total_min / 60);
    let mm = total_min % 60;

    let infoDiv = document.getElementById("info");
    let infoHpc = document.getElementById("info-hpc");

    infoDiv.innerHTML = "Grid: " + nLat + " x " + nLon +
                       " = " + totalCells.toLocaleString() + " cells.<br>" +
                       "HPC for 1 day: " + hpc_1day.toFixed(2) + " CPU-hrs.";

    infoHpc.innerHTML = "Total HPC (for " + days + " day(s)): " + hpc_total.toFixed(2) + " CPU-hrs. " +
                        "<br>Wall-time on " + cores + " cores: " + hh + " hr " + mm + " min.";
  });
</script>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML file generated: {filename}")
    print("Open it in your browser. You can draw/move the rectangle or type coords, then calculate HPC.")


if __name__ == "__main__":
    generate_leaflet_draw_hpc_html()
