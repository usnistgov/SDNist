from typing import Dict, Optional, List, Tuple
from pathlib import Path
import pandas as pd
import json
import math
import time

import sdnist.strs as strs
import sdnist.utils as u
from sdnist.report.report_data import AttachmentType, Attachment, ScorePacket, EvaluationType, \
    ReportUIData

DEID = "deid"
EPSILON = 'epsilon'
FEATURES = "features"
FEATURE_SET = "feature set"
LABELS = "labels"
LABEL_NAME = "Label Name"
LABEL_VALUE = "Label Value"
TARGET_DATASET = "target dataset"
VARIANT = "variant"
VARIANT_LABEL = "variant label"


