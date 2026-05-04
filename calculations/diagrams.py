"""Reusable inline SVG diagrams for equipment-design calculators."""
from __future__ import annotations


PUMP_SVG = """
<svg viewBox="0 0 520 220" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Centrifugal pump schematic">
  <style>
    .lbl{font: 11px 'Segoe UI', sans-serif; fill:#234A78}
    .ttl{font: bold 12px 'Segoe UI', sans-serif; fill:#0F2C4A}
    .pipe{stroke:#234A78; stroke-width:3; fill:none}
    .tank{stroke:#0F2C4A; stroke-width:2; fill:#E7F0F7}
    .arrow{fill:#234A78}
  </style>
  <text x="260" y="18" class="ttl" text-anchor="middle">Centrifugal Pump – Suction &amp; Discharge</text>
  <!-- Suction tank -->
  <rect x="20" y="60" width="90" height="110" class="tank" rx="4"/>
  <line x1="20" y1="95" x2="110" y2="95" stroke="#234A78" stroke-dasharray="4 3"/>
  <text x="65" y="50" class="lbl" text-anchor="middle">Suction tank</text>
  <text x="65" y="115" class="lbl" text-anchor="middle">Liquid</text>
  <!-- Suction pipe -->
  <line x1="110" y1="140" x2="220" y2="140" class="pipe"/>
  <text x="160" y="132" class="lbl" text-anchor="middle">Suction line</text>
  <!-- Pump body -->
  <circle cx="250" cy="140" r="28" class="tank"/>
  <circle cx="250" cy="140" r="14" fill="#234A78"/>
  <text x="250" y="190" class="lbl" text-anchor="middle">Pump</text>
  <!-- Discharge -->
  <line x1="278" y1="140" x2="380" y2="140" class="pipe"/>
  <line x1="380" y1="140" x2="380" y2="80" class="pipe"/>
  <line x1="380" y1="80" x2="480" y2="80" class="pipe"/>
  <text x="430" y="72" class="lbl" text-anchor="middle">Discharge line</text>
  <!-- Discharge tank -->
  <rect x="470" y="40" width="40" height="60" class="tank"/>
  <text x="490" y="115" class="lbl" text-anchor="middle">Vessel</text>
  <!-- Static head dim -->
  <line x1="395" y1="140" x2="395" y2="80" stroke="#6A7480" stroke-dasharray="3 2"/>
  <text x="402" y="115" class="lbl">H_static</text>
</svg>
"""


HX_SVG = """
<svg viewBox="0 0 520 220" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Shell &amp; tube heat exchanger">
  <style>
    .lbl{font:11px 'Segoe UI',sans-serif; fill:#234A78}
    .ttl{font:bold 12px 'Segoe UI',sans-serif; fill:#0F2C4A}
    .shell{stroke:#0F2C4A; stroke-width:2; fill:#E7F0F7}
    .tube{stroke:#234A78; stroke-width:1.5; fill:none}
    .arrow{stroke:#B0203A; stroke-width:2; fill:none; marker-end:url(#a)}
    .arrowc{stroke:#234A78; stroke-width:2; fill:none; marker-end:url(#a)}
  </style>
  <defs>
    <marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <polygon points="0,0 8,4 0,8" fill="#234A78"/>
    </marker>
  </defs>
  <text x="260" y="18" class="ttl" text-anchor="middle">Shell &amp; Tube Heat Exchanger (TEMA)</text>
  <!-- Shell -->
  <rect x="80" y="70" width="360" height="80" class="shell" rx="8"/>
  <!-- Tubes -->
  <line x1="80" y1="88"  x2="440" y2="88"  class="tube"/>
  <line x1="80" y1="100" x2="440" y2="100" class="tube"/>
  <line x1="80" y1="112" x2="440" y2="112" class="tube"/>
  <line x1="80" y1="124" x2="440" y2="124" class="tube"/>
  <line x1="80" y1="136" x2="440" y2="136" class="tube"/>
  <!-- Heads -->
  <rect x="60" y="62" width="22" height="96" class="shell"/>
  <rect x="438" y="62" width="22" height="96" class="shell"/>
  <!-- Shell nozzles -->
  <line x1="120" y1="70" x2="120" y2="40" class="arrowc"/>
  <text x="120" y="36" class="lbl" text-anchor="middle">Shell in</text>
  <line x1="400" y1="180" x2="400" y2="150" class="arrowc"/>
  <text x="400" y="200" class="lbl" text-anchor="middle">Shell out</text>
  <!-- Tube nozzles -->
  <line x1="40" y1="110" x2="60" y2="110" class="arrow"/>
  <text x="30" y="106" class="lbl" text-anchor="end">Tube in (hot)</text>
  <line x1="460" y1="110" x2="490" y2="110" class="arrow"/>
  <text x="495" y="106" class="lbl">Tube out</text>
  <text x="260" y="170" class="lbl" text-anchor="middle">U·A·LMTD·Ft</text>
</svg>
"""


COLUMN_SVG = """
<svg viewBox="0 0 520 320" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Distillation column">
  <style>
    .lbl{font:11px 'Segoe UI',sans-serif; fill:#234A78}
    .ttl{font:bold 12px 'Segoe UI',sans-serif; fill:#0F2C4A}
    .vsl{stroke:#0F2C4A; stroke-width:2; fill:#E7F0F7}
    .pipe{stroke:#234A78; stroke-width:2; fill:none}
    .tray{stroke:#234A78; stroke-width:1; stroke-dasharray:4 3}
  </style>
  <text x="260" y="18" class="ttl" text-anchor="middle">Distillation Column</text>
  <!-- Tower -->
  <rect x="220" y="40" width="80" height="220" class="vsl" rx="6"/>
  <!-- Trays -->
  <g class="tray">
  <line x1="220" y1="70"  x2="300" y2="70"/>
  <line x1="220" y1="90"  x2="300" y2="90"/>
  <line x1="220" y1="110" x2="300" y2="110"/>
  <line x1="220" y1="130" x2="300" y2="130"/>
  <line x1="220" y1="150" x2="300" y2="150"/>
  <line x1="220" y1="170" x2="300" y2="170"/>
  <line x1="220" y1="190" x2="300" y2="190"/>
  <line x1="220" y1="210" x2="300" y2="210"/>
  <line x1="220" y1="230" x2="300" y2="230"/>
  </g>
  <!-- Condenser -->
  <rect x="340" y="50" width="60" height="40" class="vsl"/>
  <text x="370" y="46" class="lbl" text-anchor="middle">Condenser</text>
  <line x1="300" y1="55" x2="340" y2="65" class="pipe"/>
  <!-- Reflux drum -->
  <rect x="340" y="110" width="60" height="40" class="vsl" rx="20"/>
  <text x="370" y="135" class="lbl" text-anchor="middle">Reflux</text>
  <line x1="370" y1="90" x2="370" y2="110" class="pipe"/>
  <line x1="340" y1="130" x2="260" y2="55" class="pipe"/>
  <text x="320" y="80" class="lbl">Reflux L</text>
  <!-- Distillate -->
  <line x1="400" y1="130" x2="460" y2="130" class="pipe"/>
  <text x="460" y="125" class="lbl">D, x_D</text>
  <!-- Feed -->
  <line x1="160" y1="160" x2="220" y2="160" class="pipe"/>
  <text x="155" y="156" class="lbl" text-anchor="end">Feed F, z_F</text>
  <!-- Reboiler -->
  <rect x="120" y="250" width="60" height="40" class="vsl"/>
  <text x="150" y="246" class="lbl" text-anchor="middle">Reboiler</text>
  <line x1="220" y1="255" x2="180" y2="270" class="pipe"/>
  <line x1="180" y1="265" x2="260" y2="255" class="pipe"/>
  <!-- Bottoms -->
  <line x1="260" y1="260" x2="260" y2="300" class="pipe"/>
  <text x="265" y="305" class="lbl">B, x_B</text>
</svg>
"""


SEPARATOR_SVG = """
<svg viewBox="0 0 360 280" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Vertical 2-phase separator">
  <style>
    .lbl{font:11px 'Segoe UI',sans-serif; fill:#234A78}
    .ttl{font:bold 12px 'Segoe UI',sans-serif; fill:#0F2C4A}
    .vsl{stroke:#0F2C4A; stroke-width:2; fill:#E7F0F7}
    .pipe{stroke:#234A78; stroke-width:2; fill:none}
    .liq{fill:#B4D2E7; stroke:none}
  </style>
  <text x="180" y="18" class="ttl" text-anchor="middle">Vertical 2-Phase Separator</text>
  <ellipse cx="180" cy="50" rx="60" ry="15" class="vsl"/>
  <rect x="120" y="50" width="120" height="170" class="vsl"/>
  <ellipse cx="180" cy="220" rx="60" ry="15" class="vsl"/>
  <!-- liquid -->
  <rect x="121" y="170" width="118" height="50" class="liq"/>
  <ellipse cx="180" cy="220" rx="59" ry="14" class="liq"/>
  <!-- mist eliminator -->
  <line x1="130" y1="80" x2="230" y2="80" stroke="#234A78" stroke-dasharray="3 2"/>
  <text x="245" y="83" class="lbl">Mist pad</text>
  <!-- inlet -->
  <line x1="60" y1="130" x2="120" y2="130" class="pipe"/>
  <text x="55" y="125" class="lbl" text-anchor="end">Feed (V+L)</text>
  <!-- gas out -->
  <line x1="180" y1="35" x2="180" y2="10" class="pipe"/>
  <text x="185" y="14" class="lbl">Gas out</text>
  <!-- liquid out -->
  <line x1="180" y1="235" x2="180" y2="265" class="pipe"/>
  <text x="185" y="268" class="lbl">Liquid out</text>
  <!-- Hv / Hl -->
  <line x1="100" y1="80" x2="100" y2="170" stroke="#6A7480" stroke-dasharray="3 2"/>
  <text x="92" y="125" class="lbl" text-anchor="end">Hv</text>
  <line x1="100" y1="170" x2="100" y2="220" stroke="#6A7480" stroke-dasharray="3 2"/>
  <text x="92" y="200" class="lbl" text-anchor="end">Hl</text>
</svg>
"""


PIPE_SVG = """
<svg viewBox="0 0 520 140" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Pipe line sizing">
  <style>
    .lbl{font:11px 'Segoe UI',sans-serif; fill:#234A78}
    .ttl{font:bold 12px 'Segoe UI',sans-serif; fill:#0F2C4A}
    .pipe{stroke:#0F2C4A; stroke-width:18; fill:none; stroke-linecap:round}
    .pipein{stroke:#B4D2E7; stroke-width:10; fill:none; stroke-linecap:round}
  </style>
  <text x="260" y="18" class="ttl" text-anchor="middle">Pipe Line Sizing</text>
  <line x1="40" y1="80" x2="480" y2="80" class="pipe"/>
  <line x1="40" y1="80" x2="480" y2="80" class="pipein"/>
  <text x="60" y="40" class="lbl">P1</text>
  <text x="455" y="40" class="lbl">P2</text>
  <text x="260" y="115" class="lbl" text-anchor="middle">L (m), D (m), v (m/s)</text>
  <polygon points="470,75 490,80 470,85" fill="#234A78"/>
</svg>
"""


VALVE_SVG = """
<svg viewBox="0 0 360 180" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Control valve">
  <style>
    .lbl{font:11px 'Segoe UI',sans-serif; fill:#234A78}
    .ttl{font:bold 12px 'Segoe UI',sans-serif; fill:#0F2C4A}
    .pipe{stroke:#234A78; stroke-width:3; fill:none}
    .body{stroke:#0F2C4A; stroke-width:2; fill:#E7F0F7}
  </style>
  <text x="180" y="20" class="ttl" text-anchor="middle">Control Valve – Cv Sizing</text>
  <line x1="20" y1="100" x2="140" y2="100" class="pipe"/>
  <line x1="220" y1="100" x2="340" y2="100" class="pipe"/>
  <polygon points="140,100 180,80 180,120" class="body"/>
  <polygon points="220,100 180,80 180,120" class="body"/>
  <line x1="180" y1="80" x2="180" y2="40" class="pipe"/>
  <rect x="160" y="20" width="40" height="20" class="body"/>
  <text x="40"  y="135" class="lbl">P1, T1</text>
  <text x="300" y="135" class="lbl">P2</text>
  <text x="200" y="35"  class="lbl">Actuator</text>
</svg>
"""


PSV_SVG = """
<svg viewBox="0 0 360 200" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Pressure relief valve">
  <style>
    .lbl{font:11px 'Segoe UI',sans-serif; fill:#234A78}
    .ttl{font:bold 12px 'Segoe UI',sans-serif; fill:#0F2C4A}
    .pipe{stroke:#234A78; stroke-width:3; fill:none}
    .body{stroke:#0F2C4A; stroke-width:2; fill:#E7F0F7}
  </style>
  <text x="180" y="20" class="ttl" text-anchor="middle">Pressure Relief Valve (API 520)</text>
  <line x1="20" y1="160" x2="180" y2="160" class="pipe"/>
  <line x1="180" y1="160" x2="180" y2="100" class="pipe"/>
  <polygon points="160,100 200,100 180,70" class="body"/>
  <rect x="170" y="40" width="20" height="30" class="body"/>
  <line x1="180" y1="40" x2="180" y2="20" class="pipe"/>
  <line x1="200" y1="80" x2="270" y2="80" class="pipe"/>
  <text x="40"  y="180" class="lbl">From vessel (P1)</text>
  <text x="275" y="76"  class="lbl">To flare</text>
  <text x="195" y="35"  class="lbl">Spring</text>
</svg>
"""
