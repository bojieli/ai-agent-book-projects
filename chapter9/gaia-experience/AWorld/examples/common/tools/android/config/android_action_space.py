# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from enum import Enum


class AndroidActionParamEnum(Enum):
    TAP_INDEX = "index"
    LONG_PRESS_INDEX = "index"
    INPUT_TEXT = "text"
    SWIPE_START_INDEX = "index"
    DIRECTION = "direction"
    DIST = "dist"


class DirectionParamEnum(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class DistParamEnum(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
