# Configuration package for robot control settings
# Re-export main config settings for backward compatibility

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import *
