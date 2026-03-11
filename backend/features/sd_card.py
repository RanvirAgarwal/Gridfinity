import cadquery as cq

def add_sd_slots(tray: cq.Workplane, **kwargs) -> cq.Workplane:
    """
    Modifies the single tray solid by cutting SD card vertical slots.
    """
    count = kwargs.get("count", 4)
    offset_x = kwargs.get("offset_x", 0.0)
    offset_y = kwargs.get("offset_y", 0.0)
    
    width = 2.5
    height = 25.0
    depth = 12.0
    pitch = 6.0
    
    pts = []
    for i in range(count):
        # Center the array 
        x = offset_x + (i - (count-1)/2.0) * pitch
        y = offset_y
        pts.append((x,y))

    for p in pts:
        tray = (
            tray
            .faces(">Z")
            .workplane(centerOption="CenterOfMass")
            .center(p[0], p[1])
            .rect(width, height)
            .cutBlind(-depth)
        )

    return tray
