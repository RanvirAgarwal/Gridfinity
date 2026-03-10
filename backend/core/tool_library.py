"""
Gridfinity AI — Tool Library

An in-memory database of common items with verified physical dimensions.
Used to ground the LLM outputs in real-world measurements so it never
has to hallucinate sizes.
"""

from core.schemas import ToolItem, ProfileType

# ── Seed Data ────────────────────────────────────────────────────────────────

TOOL_LIBRARY: list[ToolItem] = [
    # ── Batteries ────────────────────────────────────────────────────────
    ToolItem(
        id="bat-aa", name="AA Battery",
        aliases=["AA", "double-A", "LR6", "Mignon"],
        category="batteries",
        width=14.5, length=14.5, height=50.5,
        profile_type=ProfileType.CYLINDRICAL,
    ),
    ToolItem(
        id="bat-aaa", name="AAA Battery",
        aliases=["AAA", "triple-A", "LR03", "Micro"],
        category="batteries",
        width=10.5, length=10.5, height=44.5,
        profile_type=ProfileType.CYLINDRICAL,
    ),
    ToolItem(
        id="bat-9v", name="9V Battery",
        aliases=["9 volt", "PP3", "6LR61"],
        category="batteries",
        width=26.5, length=17.5, height=48.5,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="bat-cr2032", name="CR2032 Coin Cell",
        aliases=["CR2032", "coin cell", "button cell"],
        category="batteries",
        width=20.0, length=20.0, height=3.2,
        profile_type=ProfileType.CYLINDRICAL,
    ),
    # ── Electronics ──────────────────────────────────────────────────────
    ToolItem(
        id="elec-arduino-uno", name="Arduino Uno",
        aliases=["Arduino Uno R3", "Arduino Rev3", "Uno"],
        category="electronics",
        width=53.4, length=68.6, height=15.0,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="elec-arduino-nano", name="Arduino Nano",
        aliases=["Nano", "Arduino Nano V3"],
        category="electronics",
        width=18.0, length=45.0, height=8.0,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="elec-rpi4", name="Raspberry Pi 4",
        aliases=["RPi 4", "Pi 4", "Raspberry Pi"],
        category="electronics",
        width=56.0, length=85.0, height=17.0,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="elec-esp32", name="ESP32 DevKit",
        aliases=["ESP32", "ESP-WROOM-32"],
        category="electronics",
        width=25.4, length=48.2, height=10.0,
        profile_type=ProfileType.RECTANGULAR,
    ),
    # ── Connectors ───────────────────────────────────────────────────────
    ToolItem(
        id="conn-wago221-2", name="Wago 221-412 (2-port)",
        aliases=["Wago 221", "Wago 2-port", "Wago"],
        category="connectors",
        width=13.1, length=18.3, height=8.3,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="conn-wago221-3", name="Wago 221-413 (3-port)",
        aliases=["Wago 3-port"],
        category="connectors",
        width=18.7, length=18.3, height=8.3,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="conn-wago221-5", name="Wago 221-415 (5-port)",
        aliases=["Wago 5-port"],
        category="connectors",
        width=29.9, length=18.3, height=8.3,
        profile_type=ProfileType.RECTANGULAR,
    ),
    # ── Storage Media ────────────────────────────────────────────────────
    ToolItem(
        id="media-sd", name="SD Card",
        aliases=["SD", "SDHC", "SDXC"],
        category="storage",
        width=24.0, length=32.0, height=2.1,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="media-microsd", name="MicroSD Card",
        aliases=["microSD", "TF card"],
        category="storage",
        width=11.0, length=15.0, height=1.0,
        profile_type=ProfileType.RECTANGULAR,
    ),
    ToolItem(
        id="media-usb-a", name="USB-A Flash Drive",
        aliases=["USB stick", "thumb drive", "flash drive"],
        category="storage",
        width=12.4, length=60.0, height=4.5,
        profile_type=ProfileType.RECTANGULAR,
    ),
    # ── Hand Tools ───────────────────────────────────────────────────────
    ToolItem(
        id="tool-screwdriver-small", name="Small Screwdriver",
        aliases=["precision screwdriver", "jeweler screwdriver"],
        category="hand_tools",
        width=8.0, length=8.0, height=120.0,
        profile_type=ProfileType.CYLINDRICAL,
    ),
    ToolItem(
        id="tool-screwdriver-std", name="Standard Screwdriver",
        aliases=["screwdriver", "Phillips", "flathead"],
        category="hand_tools",
        width=12.0, length=12.0, height=150.0,
        profile_type=ProfileType.CYLINDRICAL,
    ),
    ToolItem(
        id="tool-hex-3mm", name="3mm Hex Key",
        aliases=["3mm Allen key", "Allen wrench 3mm"],
        category="hand_tools",
        width=3.5, length=70.0, height=25.0,
        profile_type=ProfileType.RECTANGULAR,
        clearance_tolerance=0.3,
    ),
    ToolItem(
        id="tool-hex-5mm", name="5mm Hex Key",
        aliases=["5mm Allen key", "Allen wrench 5mm"],
        category="hand_tools",
        width=5.5, length=90.0, height=35.0,
        profile_type=ProfileType.RECTANGULAR,
        clearance_tolerance=0.3,
    ),
    # ── Fasteners ────────────────────────────────────────────────────────
    ToolItem(
        id="fast-m3-nut", name="M3 Nut",
        aliases=["M3 hex nut"],
        category="fasteners",
        width=6.4, length=6.4, height=2.4,
        profile_type=ProfileType.CYLINDRICAL,
    ),
    ToolItem(
        id="fast-m5-bolt-20", name="M5x20 Bolt",
        aliases=["M5 bolt", "M5 screw"],
        category="fasteners",
        width=8.5, length=8.5, height=20.0,
        profile_type=ProfileType.CYLINDRICAL,
    ),
]


def search_tools(query: str) -> list[ToolItem]:
    """
    Fuzzy-search the tool library by name and aliases.
    Returns all tools whose name or any alias contains the query substring
    (case-insensitive).
    """
    q = query.lower().strip()
    if not q:
        return []

    results: list[ToolItem] = []
    for tool in TOOL_LIBRARY:
        # Check name
        if q in tool.name.lower():
            results.append(tool)
            continue
        # Check aliases
        if any(q in alias.lower() for alias in tool.aliases):
            results.append(tool)
    return results


def get_all_tools() -> list[ToolItem]:
    """Return the full tool library."""
    return TOOL_LIBRARY
