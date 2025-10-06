import usb_hid
import storage
import supervisor

# Custom 9-byte HID report descriptor:
# - 16 buttons (2 bytes)
# - 1 hat (4 bits + 4 padding)
# - 6 axes (X,Y,Z,Rx,Ry,Rz), 1 byte each
GAMEPAD_REPORT_DESCRIPTOR = bytes((
    0x05, 0x01,       # Usage Page (Generic Desktop)
    0x09, 0x05,       # Usage (Gamepad)
    0xA1, 0x01,       # Collection (Application)
    0x05, 0x09,       # Usage Page (Button)
    0x19, 0x01,       # Usage Minimum (1)
    0x29, 0x10,       # Usage Maximum (16)
    0x15, 0x00,       # Logical Minimum (0)
    0x25, 0x01,       # Logical Maximum (1)
    0x75, 0x01,       # Report Size (1)
    0x95, 0x10,       # Report Count (16)
    0x81, 0x02,       # Input (Data,Var,Abs)
    # Hat switch (4 bits) + padding (4 bits)
    0x05, 0x01,        # Usage Page (Generic Desktop)
    0x09, 0x39,        # Usage (Hat switch)
    0x15, 0x00,        # Logical Minimum (0)
    0x25, 0x07,        # Logical Maximum (7)
    0x35, 0x00,        # Physical Minimum (0)
    0x46, 0x3B, 0x01,  # Physical Maximum (315 deg)
    0x65, 0x14,        # Unit (Eng Rot: Degrees)
    0x75, 0x04,        # Report Size (4)
    0x95, 0x01,        # Report Count (1)
    0x81, 0x02,        # Input (Data,Var,Abs)
    0x75, 0x04,        # Report Size (4)
    0x95, 0x01,        # Report Count (1)
    0x81, 0x03,        # Input (Const,Var,Abs)
    # Axes (6 x 1 byte)
    0x05, 0x01,       # Usage Page (Generic Desktop)
    0x09, 0x30,       # Usage (X)
    0x09, 0x31,       # Usage (Y)
    0x09, 0x32,       # Usage (Z)
    0x09, 0x33,       # Usage (Rx)
    0x09, 0x34,       # Usage (Ry)
    0x09, 0x35,       # Usage (Rz)
    0x15, 0x00,       # Logical Minimum (0)
    0x26, 0xFF, 0x00, # Logical Maximum (255)
    0x75, 0x08,       # Report Size (8)
    0x95, 0x06,       # Report Count (6)
    0x81, 0x02,       # Input (Data,Var,Abs)
    0xC0              # End Collection
))

gamepad = usb_hid.Device(
    report_descriptor=GAMEPAD_REPORT_DESCRIPTOR,
    usage_page=0x01,  # Generic Desktop
    usage=0x05,       # Gamepad
    report_ids=(1,),  # Report ID 1
    in_report_lengths=(9,),
    out_report_lengths=(0,),
)

usb_hid.enable((gamepad,))

# --- Safety: disable drive and REPL USB ---
storage.disable_usb_drive()
supervisor.runtime.autoreload = False
