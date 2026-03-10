import os
import re
import json
import random

def build_library():
    components = {}

    # 1. Base Components (Microcontrollers, Batteries, Connectors, Keyboard, etc)
    
    # Microcontrollers
    components["arduino_uno"] = {"category": "electronics_board", "length": 68.6, "width": 53.4, "thickness": 1.6, "mount_holes": [[14, 2.5], [66, 7.5], [66, 35.5], [15.3, 50.8]]}
    components["arduino_nano"] = {"category": "electronics_board", "length": 45.0, "width": 18.0, "thickness": 1.6}
    components["esp32_devkit_v1"] = {"category": "electronics_board", "length": 54.0, "width": 27.0, "thickness": 1.6}
    components["raspberry_pi_4"] = {"category": "electronics_board", "length": 85.0, "width": 56.0, "thickness": 1.6}
    components["raspberry_pi_zero"] = {"category": "electronics_board", "length": 65.0, "width": 30.0, "thickness": 1.6}

    # Batteries
    battery_types = [
        ("18650", 18.6, 65), ("21700", 21, 70), ("26650", 26, 65),
        ("AA", 14.5, 50.5), ("AAA", 10.5, 44.5), ("C", 26.2, 50.0), ("D", 34.2, 61.5)
    ]
    for name, d, l in battery_types:
        components[name.lower()] = {"category": "battery", "diameter": d, "length": l}
        
    components["cr2032"] = {"category": "battery", "diameter": 20, "thickness": 3.2}
    components["cr2025"] = {"category": "battery", "diameter": 20, "thickness": 2.5}
    components["cr2016"] = {"category": "battery", "diameter": 20, "thickness": 1.6}

    # Metric fasteners
    for size in range(2, 13):
        components[f"m{size}"] = {
            "category": "fastener",
            "diameter": size,
            "clearance": size + 0.2,
            "head_diameter": size * 1.8
        }

    # Keyboard components
    switches = [("mx_switch", 14, 19.05), ("choc_switch", 15, 18.0)]
    for name, body, pitch in switches:
        components[name] = {"category": "keyboard_switch", "body": body, "pitch": pitch}
    components["keycap"] = {"category": "keyboard_keycap", "width": 18, "height": 10}

    # Lab Equipment
    for diameter in [10, 12, 13, 16, 18, 20, 25]:
        components[f"test_tube_{diameter}mm"] = {"category": "lab_tube", "diameter": diameter, "length": 100}
    components["centrifuge_15ml"] = {"category": "lab_tube", "diameter": 17.0, "length": 120.0}
    components["centrifuge_50ml"] = {"category": "lab_tube", "diameter": 30.0, "length": 115.0}

    # Connectors
    connectors = {
        "usb_c": [8.4, 2.6, 7.5], "usb_a": [12, 4.5, 14.0], "usb_micro": [7.4, 2.0, 6.0], 
        "hdmi": [14, 4.5, 10.0], "ethernet_rj45": [16, 14.0, 21.0]
    }
    for name, dims in connectors.items():
        components[name] = {"category": "connector", "width": dims[0], "height": dims[1], "depth": dims[2] if len(dims)>2 else 10.0}

    # Storage Media
    components["sd_card"] = {"category": "storage_media", "width": 24, "length": 32, "thickness": 2.1}
    components["micro_sd"] = {"category": "storage_media", "width": 11, "length": 15, "thickness": 1}
    components["nvme_m2"] = {"category": "storage_media", "width": 22, "length": 80, "thickness": 2.4}

    # 2. Extract from DigiKey KiCad repository
    LIB_PATH = os.path.join(os.path.dirname(__file__), "digikey-kicad-library", "digikey-footprints.pretty")
    
    if os.path.exists(LIB_PATH):
        for file in os.listdir(LIB_PATH):
            if not file.endswith(".kicad_mod"):
                continue

            name = file.replace(".kicad_mod", "").lower().replace("-", "_")
            
            with open(os.path.join(LIB_PATH, file), "r", encoding="utf-8") as f:
                data = f.read()

            pads = re.findall(r"\(pad .*?\)", data)
            
            # Very rudimentary bounding box extraction from silk screen or courtyards if possible
            # For this simplistic dataset, we'll provide footprint type and pad count
            components[name] = {
                "category": "electronic_footprint",
                "pad_count": len(pads)
            }
            
            # Simple heuristic for dimensions based on pads for faking physical width/length
            if len(pads) > 0:
                components[name]["length"] = round(max(3.0, len(pads) * 1.27), 2)
                components[name]["width"] = round(max(3.0, len(pads) * 1.27 / 2.0), 2)

    # Output JSON file
    out_file = os.path.join(os.path.dirname(__file__), "engineering_library.json")
    with open(out_file, "w") as f:
        json.dump(components, f, indent=2)

    print(f"Generated {len(components)} components into {out_file}")

if __name__ == "__main__":
    build_library()
