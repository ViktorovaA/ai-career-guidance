from enum import Enum
from typing import Optional, Dict


class Stage(str, Enum):
    START = "start"
    ASK_RIASEC = "ask_riasec"
    RIASEC_EVAL = "riasec_eval"
    ASK_MOTIVATION = "ask_motivation"
    MOTIVATION_EVAL = "motivation_eval"
    FINAL = "final"


class UserSession:
    def __init__(self):
        self.stage: Stage = Stage.START
        self.riasec_vector: Optional[Dict] = None
        self.motivation_vector: Optional[Dict] = None

    def next_stage(self):
        if self.stage == Stage.START:
            self.stage = Stage.ASK_RIASEC
        elif self.stage == Stage.ASK_RIASEC:
            self.stage = Stage.RIASEC_EVAL
        elif self.stage == Stage.RIASEC_EVAL:
            self.stage = Stage.ASK_MOTIVATION
        elif self.stage == Stage.ASK_MOTIVATION:
            self.stage = Stage.MOTIVATION_EVAL
        elif self.stage == Stage.MOTIVATION_EVAL:
            self.stage = Stage.FINAL
