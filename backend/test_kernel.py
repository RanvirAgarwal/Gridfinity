from features.base_tray import create_base_tray
from features.test_tubes import add_test_tube_rack
from features.sd_card import add_sd_slots
from features.mx_switch import add_mx_switch_tester

print("Executing Guaranteed Geometry Test Kernel...")
tray = create_base_tray(grid_x=6, grid_y=4, grid_z=3)
print(f"Base Tray generated. Volume: {tray.val().Volume():.2f}")

print("\nAdding Test Tube Holes...")
tray = add_test_tube_rack(
    tray,
    diameter=16.0,
    count=6,
    offset_x=-42.0,
    offset_y=21.0,
    grid_x=6,
    grid_y=4,
    grid_z=3
)
print(f"Volume after Test Tubes: {tray.val().Volume():.2f}")

print("\nAdding SD Card Slots...")
tray = add_sd_slots(
    tray,
    count=4,
    offset_x=42.0,
    offset_y=21.0
)
print(f"Volume after SD Cards: {tray.val().Volume():.2f}")

import cadquery as cq
import os

tmp_path = "test_kernel_output.stl"
cq.exporters.export(tray, tmp_path, "STL")
size = os.path.getsize(tmp_path)
print(f"\nGenerated test_kernel_output.stl successfully! Size: {size} bytes")
