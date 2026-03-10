import json
import os

sizes = {
    # M_size: (pitch, head_diameter, head_height, hex_size)
    2: (0.4, 3.8, 2.0, 1.5),
    2.5: (0.45, 4.5, 2.5, 2.0),
    3: (0.5, 5.5, 3.0, 2.5),
    4: (0.7, 7.0, 4.0, 3.0),
    5: (0.8, 8.5, 5.0, 4.0),
    6: (1.0, 10.0, 6.0, 5.0),
    8: (1.25, 13.0, 8.0, 6.0),
    10: (1.5, 16.0, 10.0, 8.0),
    12: (1.75, 18.0, 12.0, 10.0)
}

data = {}

for s, (pitch, hd, hh, hs) in sizes.items():
    # Convert float sizes like 2.5 to m2_5
    s_str = str(s).replace('.','_') if not isinstance(s, int) and not s.is_integer() else str(int(s))
    name_base = f"m{s_str}_socket_head_cap"
    
    # Store the generic parameter representation for the family
    data[name_base] = {
        "category": "fastener",
        "family": "metric_socket_cap_screw",
        "diameter": s,
        "pitch": pitch,
        "head_diameter": hd,
        "head_height": hh,
        "hex_size": hs,
        "clearance_hole": round(s + 0.3, 2), # Standard 3D print clearance
        "tap_hole": round(s - pitch, 2)      # Standard mechanical threading width
    }

output_path = os.path.join(os.path.dirname(__file__), "fasteners", "metric_screws.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"Generated {len(data)} metric screw families into {output_path}")
