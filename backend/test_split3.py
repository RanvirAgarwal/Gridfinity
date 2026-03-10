import cadquery as cq

try:
    print("Testing Boolean Cutter...")
    BASE_HEIGHT = 4.75
    wall_height = 21.0
    outer_w = 41.5
    outer_l = 41.5
    
    block = (
        cq.Workplane("XY")
        .workplane(offset=BASE_HEIGHT)
        .rect(outer_w, outer_l)
        .extrude(wall_height)
    )
    
    # Large 100x100mm cutter, rotated 20 degrees, cutting everything ABOVE the rotated plane
    # The origin for rotation is at the center of the original block's top face
    cutter = (
        cq.Workplane("XY")
        .workplane(offset=BASE_HEIGHT + wall_height) 
        .transformed(rotate=(20, 0, 0))
        .rect(100, 100)
        .extrude(50) # Extrude UP away from the block along the tilted Z-axis
    )
    
    block = block.cut(cutter)
    z_max = block.val().BoundingBox().zmax
    print("Cut perfectly succeeded! Max Z:", z_max)
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Cut failed:", e)
