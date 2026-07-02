from enum import IntEnum


class ControlLogicEnum(IntEnum):
    """
        This IntEnum handles indexing for the control logic. Clients
        should reference these enums when sending RPC commands.
    """
    FSM5 = 0,
    PROPORTIONAL = 1,
    STANDING = 2