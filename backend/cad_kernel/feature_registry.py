from features.base_tray import create_base_tray
from features.test_tubes import add_test_tube_rack
from features.sd_card import add_sd_slots
from features.raspberry_pi import add_raspberry_pi_mount
from features.mx_switch import add_mx_switch_tester

FEATURE_REGISTRY = {
    "base_tray": create_base_tray,
    "gridfinity_base": create_base_tray,
    "basic_storage_bin": create_base_tray,
    "test_tube_rack_16mm": add_test_tube_rack,
    "sd_card": add_sd_slots,
    "raspberry_pi": add_raspberry_pi_mount,
    "mx_switch_tester": add_mx_switch_tester
}
