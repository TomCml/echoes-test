# Legacy opcodes (keeping for backward compatibility)
from . import damage as legacy_damage
from . import apply_status
from . import bonus_damage_if_target_has_status
from . import build_gauge
from . import heal
from . import modify_stat
from . import remove_status
from . import shield

# New categorized opcodes
from .damage import *
from .healing import *
from .shields import *
from .status_effects import *
from .stat_modifiers import *
from .gauge import *
from .triggers import *
from .cooldown import *
from .summons import *
from .misc import *
