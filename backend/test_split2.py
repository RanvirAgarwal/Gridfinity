import cadquery as cq

try:
    print("Testing angled ring block split...")
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
    # Print max Z of block
    print("Max Z before cut:", block.val().BoundingBox().zmax)
    
    block = block.faces(">Z").workplane(offset=-0.1).transformed(rotate=(20, 0, 0)).split(keepTop=False)
    print("Angled split succeeded!")
    print("Max Z after cut:", block.val().BoundingBox().zmax)
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Angled split failed:", e)
