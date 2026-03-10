import cadquery as cq

try:
    print("Testing standard split...")
    block = cq.Workplane("XY").rect(40, 40).extrude(20)
    # Origin is strictly on the top face
    sliced = block.faces(">Z").workplane().transformed(rotate=(15, 0, 0)).split(keepTop=False)
    print("Standard split succeeded!")
except Exception as e:
    print("Standard split failed:", e)

try:
    print("Testing offset split...")
    block2 = cq.Workplane("XY").rect(40, 40).extrude(20)
    # Offset by -0.1mm to cleanly penetrate the solid
    sliced2 = block2.faces(">Z").workplane(offset=-0.1).transformed(rotate=(15, 0, 0)).split(keepTop=False)
    print("Offset split succeeded!")
except Exception as e:
    print("Offset split failed:", e)
