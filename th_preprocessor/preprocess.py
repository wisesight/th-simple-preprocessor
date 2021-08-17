import html
import re
import unicodedata
from datetime import datetime
from typing import Iterable, List, Set, Tuple, Union

import emoji

from th_preprocessor.data import (
    ACCENTED_PAIRS,
    THAI_NORMALIZE_PAIRS,
    THAI_STOPWORDS,
    THAI_TO_ARABIC_DIGIT_PAIRS,
    TOKENIZE_PAIRS,
)

COMBINED_NORMALIZE_PAIRS = (
    THAI_NORMALIZE_PAIRS + THAI_TO_ARABIC_DIGIT_PAIRS + TOKENIZE_PAIRS
)

# Words to be used as replacement
# (normalization for better classification, we hope)
REPLACE_LINK = " WSLINK "
REPLACE_EMAIL = " WSEMAIL "
REPLACE_AT_MENTION = " WSNAME "
REPLACE_HAHA = " WSHAHA "
REPLACE_NUMBER = " WSNUMBER "
REPLACE_PHONE = " WSPHONE "
REPLACE_DATE = " WSDATE "

# Check word class
RE_NUM = re.compile(r"[+\-]?(?:[0-9๑๒๓๔๕๖๗๘๙๐]+,?)+(?:\.[0-9๑๒๓๔๕๖๗๘๙๐]*)?")
RE_NUM2 = re.compile(r"[+\-]?(?:[0-9๑๒๓๔๕๖๗๘๙๐]+,?){2,}(?:\.[0-9๑๒๓๔๕๖๗๘๙๐]*)?")
RE_THAI = re.compile(r"[\u0E00-\u0E7F0-9\s]+")
RE_LATIN = re.compile(r"[a-zA-Z0-9\s]+")

# <tag>, http://, www., .php, @mention, mail@address.com, hahaha, 555, 1234
# To be normalized
RE_TAG = re.compile(r"<[^>]+>")
RE_HTTP_WWW = re.compile(r"(?:\b\S{3,}:\/{1,}\S*)|(?:[wW]{2,}\.\S+)")
RE_EXT = re.compile(
    r"\w+\.(html|htm|shtm|shtml|cgi|php|php3|asp|aspx|cfm|cfml|jsp|png|gif|jpg|java|class|webp|mp3|mp4|mov|pl|do)(\?\S*)?\b",
    flags=re.IGNORECASE,
)
RE_AT_MENTION = re.compile(r"(?:^|\s)@\S+")
RE_EMAIL = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
RE_HAHA = re.compile(r"\b(?:ha\s*){2,}|\u0E16{3,}|5{3,}(?!.\d)\b", flags=re.IGNORECASE)
RE_HASHTAGS = re.compile(r"#([a-zA-Zก-๛0-9]+[a-zA-Zก-๛0-9]*)")

# Phone numbers
phone_body_patterns = [
    r"\b[0๐]\s*[.-]?\s*[0-9๐-๙]{4}\s*[.-]?\s*[0-9๐-๙]{4}\b",  # 0-1234-5678
    r"\b[0๐][0-9๐-๙]{2}\s*[.-]?\s*[0-9๐-๙]{3}\s*[.-]?\s*[0-9๐-๙]{3,4}\b",  # 012-345-678
    r"\b[0๐]\s*[.-]?\s*[0-9๐-๙]{3}\s*[.-]?\s*[0-9๐-๙]{3}\s*[.-]?\s*[0-9๐-๙]{3,4}\b",  # 0-123-456-789
    r"\b[0๐][0-9๐-๙]\s*[.-]?\s*[0-9๐-๙]{4}\s*[.-]?\s*[0-9๐-๙]{4}\b",  # 01-2345-6789
    r"\b[0๐][0-9๐-๙]{9}\b",  # 0123456789
    r"\b[01๐๑]\s*[.-]?\s*[8๘][0-9๐-๙]{2}\s*[.-]?\s*[0-9๐-๙]{3,4}\s*[.-]?\s*[0-9๐-๙]{3,4}\b",  # 1-800-123-4567
    r"\b\([0-9๐-๙]{2,3}\)\s*[.-]?\s*[0-9๐-๙]{3,4}\s*[.-]?\s*[0-9๐-๙]{3,4}\b",  # (01) 234 5678
]
phone_area_patterns = [
    r"(\+[0-9๐-๙]{2,3}\s?)?",  # +66
    r"(\([0-9๐-๙]{2,3}\)\s?)?",  # (66)
]
phone_ext_patterns = r"(\s?(x|X|Ext|EXT|ext|ต่อ|กด)\.?\s?e[0-9๐-๙]{1,4})?"
phone_regex = (
    "("
    + "|".join(phone_area_patterns)
    + ")("
    + "|".join(phone_body_patterns)
    + ")"
    + phone_ext_patterns
)
RE_PHONE = re.compile(phone_regex)

# Duplicated characters: aaaa, ! ! ! !, ะะะะะ
RE_DUP_C_C = re.compile(r"(?:^|\s)(\S{1,5})(\s+\1)+")  # duplicated isolated chars/words
RE_DUP_CC = re.compile(r"(\D{2,})\1{3,}")  # duplicated non-digits
RE_DUP_C6 = re.compile(r"(\D)\1{5,}")  # duplicated non-digits (six or more characters)
RE_DUP_THAI = re.compile(
    r"([\u0E2F-\u0E3A\u0E3F\u0E40-\u0E4F\?\!])\1+"
)  # Thai vowels/symbols


# Duplicated whitespaces: spaces, tabs, empty lines, leading/trailing spaces
RE_DUP_SPACE = re.compile(r"[\t ]{2,}")
RE_DUP_EMPTYLINE = re.compile(r"[\t ]*\n([\t ]*\n)*")
RE_STRIP = re.compile(r"(?:(?<=\n)[\t ]+)|(?:[\t ]+(?=\n))")

# Adjacent characters in different class
RE_DIGIT_NONDIGIT = re.compile(r"([\d\.,])(\D)")  # (Digit)(Non-Digit)
RE_NONDIGIT_DIGIT = re.compile(r"(\D)([\d\.,])")  # (Non-Digit)(Digit)
RE_THAI_NONTHAI = re.compile(
    r"([\u0E00-\u0E4F])([^\u0E00-\u0E4F\s])"
)  # (Thai)(Non-Thai)
RE_NONTHAI_THAI = re.compile(
    r"([^\u0E00-\u0E4F\s])([\u0E00-\u0E4F])"
)  # (Non-Thai)(Thai)
RE_LATIN_NONLATIN = re.compile(r"([a-zA-Z])([^a-zA-Z\s])")  # (Latin)(Non-Latin)
RE_NONLATIN_LATIN = re.compile(r"([^a-zA-Z\s])([a-zA-Z])")  # (Non-Latin)(Latin)

RE_EMOJI = emoji.get_emoji_regexp()  # use pre-complied pattern from emoji library
RE_NONTHAI_ENG_EMOJI = re.compile(
    r"[^\u0E00-\u0E7Fa-zA-Z!?👨\u200d❤️\u200d💋\u200d👨|👩\u200d❤️\u200d💋\u200d👨|👩\u200d❤️\u200d💋\u200d👩|🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f|🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f|🏴\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f|👨\u200d👨\u200d👦\u200d👦|👨\u200d👨\u200d👧\u200d👦|👨\u200d👨\u200d👧\u200d👧|👨\u200d👩\u200d👦\u200d👦|👨\u200d👩\u200d👧\u200d👦|👨\u200d👩\u200d👧\u200d👧|👩\u200d👩\u200d👦\u200d👦|👩\u200d👩\u200d👧\u200d👦|👩\u200d👩\u200d👧\u200d👧|👨\u200d❤️\u200d👨|👩\u200d❤️\u200d👨|👩\u200d❤️\u200d👩|👱🏿\u200d♂️|👱🏻\u200d♂️|👱🏾\u200d♂️|👱🏼\u200d♂️|👱🏽\u200d♂️|👱🏿\u200d♀️|👱🏻\u200d♀️|👱🏾\u200d♀️|👱🏼\u200d♀️|👱🏽\u200d♀️|👁️\u200d🗨️|👨\u200d👦\u200d👦|👨\u200d👧\u200d👦|👨\u200d👧\u200d👧|👨\u200d👨\u200d👦|👨\u200d👨\u200d👧|👨\u200d👩\u200d👦|👨\u200d👩\u200d👧|👩\u200d👦\u200d👦|👩\u200d👧\u200d👦|👩\u200d👧\u200d👧|👩\u200d👩\u200d👦|👩\u200d👩\u200d👧|🚴🏿\u200d♂️|🚴🏻\u200d♂️|🚴🏾\u200d♂️|🚴🏼\u200d♂️|🚴🏽\u200d♂️|⛹️\u200d♂️|⛹🏿\u200d♂️|⛹🏻\u200d♂️|⛹🏾\u200d♂️|⛹🏼\u200d♂️|⛹🏽\u200d♂️|🙇🏿\u200d♂️|🙇🏻\u200d♂️|🙇🏾\u200d♂️|🙇🏼\u200d♂️|🙇🏽\u200d♂️|🤸🏿\u200d♂️|🤸🏻\u200d♂️|🤸🏾\u200d♂️|🤸🏼\u200d♂️|🤸🏽\u200d♂️|🧗🏿\u200d♂️|🧗🏻\u200d♂️|🧗🏾\u200d♂️|🧗🏼\u200d♂️|🧗🏽\u200d♂️|👷🏿\u200d♂️|👷🏻\u200d♂️|👷🏾\u200d♂️|👷🏼\u200d♂️|👷🏽\u200d♂️|🕵️\u200d♂️|🕵🏿\u200d♂️|🕵🏻\u200d♂️|🕵🏾\u200d♂️|🕵🏼\u200d♂️|🕵🏽\u200d♂️|🧝🏿\u200d♂️|🧝🏻\u200d♂️|🧝🏾\u200d♂️|🧝🏼\u200d♂️|🧝🏽\u200d♂️|🤦🏿\u200d♂️|🤦🏻\u200d♂️|🤦🏾\u200d♂️|🤦🏼\u200d♂️|🤦🏽\u200d♂️|🧚🏿\u200d♂️|🧚🏻\u200d♂️|🧚🏾\u200d♂️|🧚🏼\u200d♂️|🧚🏽\u200d♂️|🙍🏿\u200d♂️|🙍🏻\u200d♂️|🙍🏾\u200d♂️|🙍🏼\u200d♂️|🙍🏽\u200d♂️|🙅🏿\u200d♂️|🙅🏻\u200d♂️|🙅🏾\u200d♂️|🙅🏼\u200d♂️|🙅🏽\u200d♂️|🙆🏿\u200d♂️|🙆🏻\u200d♂️|🙆🏾\u200d♂️|🙆🏼\u200d♂️|🙆🏽\u200d♂️|💇🏿\u200d♂️|💇🏻\u200d♂️|💇🏾\u200d♂️|💇🏼\u200d♂️|💇🏽\u200d♂️|💆🏿\u200d♂️|💆🏻\u200d♂️|💆🏾\u200d♂️|💆🏼\u200d♂️|💆🏽\u200d♂️|🏌️\u200d♂️|🏌🏿\u200d♂️|🏌🏻\u200d♂️|🏌🏾\u200d♂️|🏌🏼\u200d♂️|🏌🏽\u200d♂️|💂🏿\u200d♂️|💂🏻\u200d♂️|💂🏾\u200d♂️|💂🏼\u200d♂️|💂🏽\u200d♂️|👨🏿\u200d⚕️|👨🏻\u200d⚕️|👨🏾\u200d⚕️|👨🏼\u200d⚕️|👨🏽\u200d⚕️|🧘🏿\u200d♂️|🧘🏻\u200d♂️|🧘🏾\u200d♂️|🧘🏼\u200d♂️|🧘🏽\u200d♂️|🧖🏿\u200d♂️|🧖🏻\u200d♂️|🧖🏾\u200d♂️|🧖🏼\u200d♂️|🧖🏽\u200d♂️|👨🏿\u200d⚖️|👨🏻\u200d⚖️|👨🏾\u200d⚖️|👨🏼\u200d⚖️|👨🏽\u200d⚖️|🤹🏿\u200d♂️|🤹🏻\u200d♂️|🤹🏾\u200d♂️|🤹🏼\u200d♂️|🤹🏽\u200d♂️|🏋️\u200d♂️|🏋🏿\u200d♂️|🏋🏻\u200d♂️|🏋🏾\u200d♂️|🏋🏼\u200d♂️|🏋🏽\u200d♂️|🧙🏿\u200d♂️|🧙🏻\u200d♂️|🧙🏾\u200d♂️|🧙🏼\u200d♂️|🧙🏽\u200d♂️|🚵🏿\u200d♂️|🚵🏻\u200d♂️|🚵🏾\u200d♂️|🚵🏼\u200d♂️|🚵🏽\u200d♂️|👨🏿\u200d✈️|👨🏻\u200d✈️|👨🏾\u200d✈️|👨🏼\u200d✈️|👨🏽\u200d✈️|🤾🏿\u200d♂️|🤾🏻\u200d♂️|🤾🏾\u200d♂️|🤾🏼\u200d♂️|🤾🏽\u200d♂️|🤽🏿\u200d♂️|🤽🏻\u200d♂️|🤽🏾\u200d♂️|🤽🏼\u200d♂️|🤽🏽\u200d♂️|👮🏿\u200d♂️|👮🏻\u200d♂️|👮🏾\u200d♂️|👮🏼\u200d♂️|👮🏽\u200d♂️|🙎🏿\u200d♂️|🙎🏻\u200d♂️|🙎🏾\u200d♂️|🙎🏼\u200d♂️|🙎🏽\u200d♂️|🙋🏿\u200d♂️|🙋🏻\u200d♂️|🙋🏾\u200d♂️|🙋🏼\u200d♂️|🙋🏽\u200d♂️|🚣🏿\u200d♂️|🚣🏻\u200d♂️|🚣🏾\u200d♂️|🚣🏼\u200d♂️|🚣🏽\u200d♂️|🏃🏿\u200d♂️|🏃🏻\u200d♂️|🏃🏾\u200d♂️|🏃🏼\u200d♂️|🏃🏽\u200d♂️|🤷🏿\u200d♂️|🤷🏻\u200d♂️|🤷🏾\u200d♂️|🤷🏼\u200d♂️|🤷🏽\u200d♂️|🏄🏿\u200d♂️|🏄🏻\u200d♂️|🏄🏾\u200d♂️|🏄🏼\u200d♂️|🏄🏽\u200d♂️|🏊🏿\u200d♂️|🏊🏻\u200d♂️|🏊🏾\u200d♂️|🏊🏼\u200d♂️|🏊🏽\u200d♂️|💁🏿\u200d♂️|💁🏻\u200d♂️|💁🏾\u200d♂️|💁🏼\u200d♂️|💁🏽\u200d♂️|🧛🏿\u200d♂️|🧛🏻\u200d♂️|🧛🏾\u200d♂️|🧛🏼\u200d♂️|🧛🏽\u200d♂️|🚶🏿\u200d♂️|🚶🏻\u200d♂️|🚶🏾\u200d♂️|🚶🏼\u200d♂️|🚶🏽\u200d♂️|👳🏿\u200d♂️|👳🏻\u200d♂️|👳🏾\u200d♂️|👳🏼\u200d♂️|👳🏽\u200d♂️|🧜🏿\u200d♀️|🧜🏻\u200d♀️|🧜🏾\u200d♀️|🧜🏼\u200d♀️|🧜🏽\u200d♀️|🧜🏿\u200d♂️|🧜🏻\u200d♂️|🧜🏾\u200d♂️|🧜🏼\u200d♂️|🧜🏽\u200d♂️|🧑\u200d🤝\u200d🧑|🚴🏿\u200d♀️|🚴🏻\u200d♀️|🚴🏾\u200d♀️|🚴🏼\u200d♀️|🚴🏽\u200d♀️|⛹️\u200d♀️|⛹🏿\u200d♀️|⛹🏻\u200d♀️|⛹🏾\u200d♀️|⛹🏼\u200d♀️|⛹🏽\u200d♀️|🙇🏿\u200d♀️|🙇🏻\u200d♀️|🙇🏾\u200d♀️|🙇🏼\u200d♀️|🙇🏽\u200d♀️|🤸🏿\u200d♀️|🤸🏻\u200d♀️|🤸🏾\u200d♀️|🤸🏼\u200d♀️|🤸🏽\u200d♀️|🧗🏿\u200d♀️|🧗🏻\u200d♀️|🧗🏾\u200d♀️|🧗🏼\u200d♀️|🧗🏽\u200d♀️|👷🏿\u200d♀️|👷🏻\u200d♀️|👷🏾\u200d♀️|👷🏼\u200d♀️|👷🏽\u200d♀️|🕵️\u200d♀️|🕵🏿\u200d♀️|🕵🏻\u200d♀️|🕵🏾\u200d♀️|🕵🏼\u200d♀️|🕵🏽\u200d♀️|🧝🏿\u200d♀️|🧝🏻\u200d♀️|🧝🏾\u200d♀️|🧝🏼\u200d♀️|🧝🏽\u200d♀️|🤦🏿\u200d♀️|🤦🏻\u200d♀️|🤦🏾\u200d♀️|🤦🏼\u200d♀️|🤦🏽\u200d♀️|🧚🏿\u200d♀️|🧚🏻\u200d♀️|🧚🏾\u200d♀️|🧚🏼\u200d♀️|🧚🏽\u200d♀️|🙍🏿\u200d♀️|🙍🏻\u200d♀️|🙍🏾\u200d♀️|🙍🏼\u200d♀️|🙍🏽\u200d♀️|🙅🏿\u200d♀️|🙅🏻\u200d♀️|🙅🏾\u200d♀️|🙅🏼\u200d♀️|🙅🏽\u200d♀️|🙆🏿\u200d♀️|🙆🏻\u200d♀️|🙆🏾\u200d♀️|🙆🏼\u200d♀️|🙆🏽\u200d♀️|💇🏿\u200d♀️|💇🏻\u200d♀️|💇🏾\u200d♀️|💇🏼\u200d♀️|💇🏽\u200d♀️|💆🏿\u200d♀️|💆🏻\u200d♀️|💆🏾\u200d♀️|💆🏼\u200d♀️|💆🏽\u200d♀️|🏌️\u200d♀️|🏌🏿\u200d♀️|🏌🏻\u200d♀️|🏌🏾\u200d♀️|🏌🏼\u200d♀️|🏌🏽\u200d♀️|💂🏿\u200d♀️|💂🏻\u200d♀️|💂🏾\u200d♀️|💂🏼\u200d♀️|💂🏽\u200d♀️|👩🏿\u200d⚕️|👩🏻\u200d⚕️|👩🏾\u200d⚕️|👩🏼\u200d⚕️|👩🏽\u200d⚕️|🧘🏿\u200d♀️|🧘🏻\u200d♀️|🧘🏾\u200d♀️|🧘🏼\u200d♀️|🧘🏽\u200d♀️|🧖🏿\u200d♀️|🧖🏻\u200d♀️|🧖🏾\u200d♀️|🧖🏼\u200d♀️|🧖🏽\u200d♀️|👩🏿\u200d⚖️|👩🏻\u200d⚖️|👩🏾\u200d⚖️|👩🏼\u200d⚖️|👩🏽\u200d⚖️|🤹🏿\u200d♀️|🤹🏻\u200d♀️|🤹🏾\u200d♀️|🤹🏼\u200d♀️|🤹🏽\u200d♀️|🏋️\u200d♀️|🏋🏿\u200d♀️|🏋🏻\u200d♀️|🏋🏾\u200d♀️|🏋🏼\u200d♀️|🏋🏽\u200d♀️|🧙🏿\u200d♀️|🧙🏻\u200d♀️|🧙🏾\u200d♀️|🧙🏼\u200d♀️|🧙🏽\u200d♀️|🚵🏿\u200d♀️|🚵🏻\u200d♀️|🚵🏾\u200d♀️|🚵🏼\u200d♀️|🚵🏽\u200d♀️|👩🏿\u200d✈️|👩🏻\u200d✈️|👩🏾\u200d✈️|👩🏼\u200d✈️|👩🏽\u200d✈️|🤾🏿\u200d♀️|🤾🏻\u200d♀️|🤾🏾\u200d♀️|🤾🏼\u200d♀️|🤾🏽\u200d♀️|🤽🏿\u200d♀️|🤽🏻\u200d♀️|🤽🏾\u200d♀️|🤽🏼\u200d♀️|🤽🏽\u200d♀️|👮🏿\u200d♀️|👮🏻\u200d♀️|👮🏾\u200d♀️|👮🏼\u200d♀️|👮🏽\u200d♀️|🙎🏿\u200d♀️|🙎🏻\u200d♀️|🙎🏾\u200d♀️|🙎🏼\u200d♀️|🙎🏽\u200d♀️|🙋🏿\u200d♀️|🙋🏻\u200d♀️|🙋🏾\u200d♀️|🙋🏼\u200d♀️|🙋🏽\u200d♀️|🚣🏿\u200d♀️|🚣🏻\u200d♀️|🚣🏾\u200d♀️|🚣🏼\u200d♀️|🚣🏽\u200d♀️|🏃🏿\u200d♀️|🏃🏻\u200d♀️|🏃🏾\u200d♀️|🏃🏼\u200d♀️|🏃🏽\u200d♀️|🤷🏿\u200d♀️|🤷🏻\u200d♀️|🤷🏾\u200d♀️|🤷🏼\u200d♀️|🤷🏽\u200d♀️|🏄🏿\u200d♀️|🏄🏻\u200d♀️|🏄🏾\u200d♀️|🏄🏼\u200d♀️|🏄🏽\u200d♀️|🏊🏿\u200d♀️|🏊🏻\u200d♀️|🏊🏾\u200d♀️|🏊🏼\u200d♀️|🏊🏽\u200d♀️|💁🏿\u200d♀️|💁🏻\u200d♀️|💁🏾\u200d♀️|💁🏼\u200d♀️|💁🏽\u200d♀️|🧛🏿\u200d♀️|🧛🏻\u200d♀️|🧛🏾\u200d♀️|🧛🏼\u200d♀️|🧛🏽\u200d♀️|🚶🏿\u200d♀️|🚶🏻\u200d♀️|🚶🏾\u200d♀️|🚶🏼\u200d♀️|🚶🏽\u200d♀️|👳🏿\u200d♀️|👳🏻\u200d♀️|👳🏾\u200d♀️|👳🏼\u200d♀️|👳🏽\u200d♀️|👱\u200d♂️|👱\u200d♀️|👨🏿\u200d🎨|👨🏻\u200d🎨|👨🏾\u200d🎨|👨🏼\u200d🎨|👨🏽\u200d🎨|👨🏿\u200d🚀|👨🏻\u200d🚀|👨🏾\u200d🚀|👨🏼\u200d🚀|👨🏽\u200d🚀|🚴\u200d♂️|🙇\u200d♂️|🤸\u200d♂️|🧗\u200d♂️|👷\u200d♂️|👨🏿\u200d🍳|👨🏻\u200d🍳|👨🏾\u200d🍳|👨🏼\u200d🍳|👨🏽\u200d🍳|🧝\u200d♂️|🤦\u200d♂️|👨🏿\u200d🏭|👨🏻\u200d🏭|👨🏾\u200d🏭|👨🏼\u200d🏭|👨🏽\u200d🏭|🧚\u200d♂️|👨🏿\u200d🌾|👨🏻\u200d🌾|👨🏾\u200d🌾|👨🏼\u200d🌾|👨🏽\u200d🌾|👨🏿\u200d🚒|👨🏻\u200d🚒|👨🏾\u200d🚒|👨🏼\u200d🚒|👨🏽\u200d🚒|🙍\u200d♂️|🧞\u200d♂️|🙅\u200d♂️|🙆\u200d♂️|💇\u200d♂️|💆\u200d♂️|💂\u200d♂️|👨\u200d⚕️|🧘\u200d♂️|🧖\u200d♂️|👨\u200d⚖️|🤹\u200d♂️|🧙\u200d♂️|👨🏿\u200d🔧|👨🏻\u200d🔧|👨🏾\u200d🔧|👨🏼\u200d🔧|👨🏽\u200d🔧|🚵\u200d♂️|👨🏿\u200d💼|👨🏻\u200d💼|👨🏾\u200d💼|👨🏼\u200d💼|👨🏽\u200d💼|👨\u200d✈️|🤾\u200d♂️|🤽\u200d♂️|👮\u200d♂️|🙎\u200d♂️|🙋\u200d♂️|🚣\u200d♂️|🏃\u200d♂️|👨🏿\u200d🔬|👨🏻\u200d🔬|👨🏾\u200d🔬|👨🏼\u200d🔬|👨🏽\u200d🔬|🤷\u200d♂️|👨🏿\u200d🎤|👨🏻\u200d🎤|👨🏾\u200d🎤|👨🏼\u200d🎤|👨🏽\u200d🎤|👨🏿\u200d🎓|👨🏻\u200d🎓|👨🏾\u200d🎓|👨🏼\u200d🎓|👨🏽\u200d🎓|🏄\u200d♂️|🏊\u200d♂️|👨🏿\u200d🏫|👨🏻\u200d🏫|👨🏾\u200d🏫|👨🏼\u200d🏫|👨🏽\u200d🏫|👨🏿\u200d💻|👨🏻\u200d💻|👨🏾\u200d💻|👨🏼\u200d💻|👨🏽\u200d💻|💁\u200d♂️|🧛\u200d♂️|🚶\u200d♂️|👳\u200d♂️|🧟\u200d♂️|👯\u200d♂️|🤼\u200d♂️|🧜\u200d♀️|🧜\u200d♂️|🏴\u200d☠️|🏳️\u200d🌈|👩🏿\u200d🎨|👩🏻\u200d🎨|👩🏾\u200d🎨|👩🏼\u200d🎨|👩🏽\u200d🎨|👩🏿\u200d🚀|👩🏻\u200d🚀|👩🏾\u200d🚀|👩🏼\u200d🚀|👩🏽\u200d🚀|🚴\u200d♀️|🙇\u200d♀️|🤸\u200d♀️|🧗\u200d♀️|👷\u200d♀️|👩🏿\u200d🍳|👩🏻\u200d🍳|👩🏾\u200d🍳|👩🏼\u200d🍳|👩🏽\u200d🍳|🧝\u200d♀️|🤦\u200d♀️|👩🏿\u200d🏭|👩🏻\u200d🏭|👩🏾\u200d🏭|👩🏼\u200d🏭|👩🏽\u200d🏭|🧚\u200d♀️|👩🏿\u200d🌾|👩🏻\u200d🌾|👩🏾\u200d🌾|👩🏼\u200d🌾|👩🏽\u200d🌾|👩🏿\u200d🚒|👩🏻\u200d🚒|👩🏾\u200d🚒|👩🏼\u200d🚒|👩🏽\u200d🚒|🙍\u200d♀️|🧞\u200d♀️|🙅\u200d♀️|🙆\u200d♀️|💇\u200d♀️|💆\u200d♀️|💂\u200d♀️|👩\u200d⚕️|🧘\u200d♀️|🧖\u200d♀️|👩\u200d⚖️|🤹\u200d♀️|🧙\u200d♀️|👩🏿\u200d🔧|👩🏻\u200d🔧|👩🏾\u200d🔧|👩🏼\u200d🔧|👩🏽\u200d🔧|🚵\u200d♀️|👩🏿\u200d💼|👩🏻\u200d💼|👩🏾\u200d💼|👩🏼\u200d💼|👩🏽\u200d💼|👩\u200d✈️|🤾\u200d♀️|🤽\u200d♀️|👮\u200d♀️|🙎\u200d♀️|🙋\u200d♀️|🚣\u200d♀️|🏃\u200d♀️|👩🏿\u200d🔬|👩🏻\u200d🔬|👩🏾\u200d🔬|👩🏼\u200d🔬|👩🏽\u200d🔬|🤷\u200d♀️|👩🏿\u200d🎤|👩🏻\u200d🎤|👩🏾\u200d🎤|👩🏼\u200d🎤|👩🏽\u200d🎤|👩🏿\u200d🎓|👩🏻\u200d🎓|👩🏾\u200d🎓|👩🏼\u200d🎓|👩🏽\u200d🎓|🏄\u200d♀️|🏊\u200d♀️|👩🏿\u200d🏫|👩🏻\u200d🏫|👩🏾\u200d🏫|👩🏼\u200d🏫|👩🏽\u200d🏫|👩🏿\u200d💻|👩🏻\u200d💻|👩🏾\u200d💻|👩🏼\u200d💻|👩🏽\u200d💻|💁\u200d♀️|🧛\u200d♀️|🚶\u200d♀️|👳\u200d♀️|🧟\u200d♀️|👯\u200d♀️|🤼\u200d♀️|👨\u200d🦲|👩\u200d🦲|👨\u200d🦱|👩\u200d🦱|👨\u200d👦|👨\u200d👧|👩\u200d👦|👩\u200d👧|\#️⃣|\*️⃣|0️⃣|1️⃣|2️⃣|3️⃣|4️⃣|5️⃣|6️⃣|7️⃣|8️⃣|9️⃣|👨\u200d🎨|👨\u200d🚀|👨\u200d🍳|👨\u200d🏭|👨\u200d🌾|👨\u200d🚒|👨\u200d\U0001f9bd|👨\u200d\U0001f9bc|👨\u200d🔧|👨\u200d💼|👨\u200d🔬|👨\u200d🎤|👨\u200d🎓|👨\u200d🏫|👨\u200d💻|👨\u200d\U0001f9af|👨\u200d🦰|👩\u200d🦰|🐕\u200d\U0001f9ba|👨\u200d🦳|👩\u200d🦳|👩\u200d🎨|👩\u200d🚀|👩\u200d🍳|👩\u200d🏭|👩\u200d🌾|👩\u200d🚒|👩\u200d\U0001f9bd|👩\u200d\U0001f9bc|👩\u200d🔧|👩\u200d💼|👩\u200d🔬|👩\u200d🎤|👩\u200d🎓|👩\u200d🏫|👩\u200d💻|👩\u200d\U0001f9af|🇦🇫|🇦🇱|🇩🇿|🇦🇸|🇦🇩|🇦🇴|🇦🇮|🇦🇶|🇦🇬|🇦🇷|🇦🇲|🇦🇼|🇦🇨|🇦🇺|🇦🇹|🇦🇿|🇧🇸|🇧🇭|🇧🇩|🇧🇧|🇧🇾|🇧🇪|🇧🇿|🇧🇯|🇧🇲|🇧🇹|🇧🇴|🇧🇦|🇧🇼|🇧🇻|🇧🇷|🇮🇴|🇻🇬|🇧🇳|🇧🇬|🇧🇫|🇧🇮|🇰🇭|🇨🇲|🇨🇦|🇮🇨|🇨🇻|🇧🇶|🇰🇾|🇨🇫|🇪🇦|🇹🇩|🇨🇱|🇨🇳|🇨🇽|🇨🇵|🇨🇨|🇨🇴|🇰🇲|🇨🇬|🇨🇩|🇨🇰|🇨🇷|🇭🇷|🇨🇺|🇨🇼|🇨🇾|🇨🇿|🇨🇮|🇩🇰|🇩🇬|🇩🇯|🇩🇲|🇩🇴|🇪🇨|🇪🇬|🇸🇻|🇬🇶|🇪🇷|🇪🇪|🇪🇹|🇪🇺|🇫🇰|🇫🇴|🇫🇯|🇫🇮|🇫🇷|🇬🇫|🇵🇫|🇹🇫|🇬🇦|🇬🇲|🇬🇪|🇩🇪|🇬🇭|🇬🇮|🇬🇷|🇬🇱|🇬🇩|🇬🇵|🇬🇺|🇬🇹|🇬🇬|🇬🇳|🇬🇼|🇬🇾|🇭🇹|🇭🇲|🇭🇳|🇭🇰|🇭🇺|🇮🇸|🇮🇳|🇮🇩|🇮🇷|🇮🇶|🇮🇪|🇮🇲|🇮🇱|🇮🇹|🇯🇲|🇯🇵|🇯🇪|🇯🇴|🇰🇿|🇰🇪|🇰🇮|🇽🇰|🇰🇼|🇰🇬|🇱🇦|🇱🇻|🇱🇧|🇱🇸|🇱🇷|🇱🇾|🇱🇮|🇱🇹|🇱🇺|🇲🇴|🇲🇰|🇲🇬|🇲🇼|🇲🇾|🇲🇻|🇲🇱|🇲🇹|🇲🇭|🇲🇶|🇲🇷|🇲🇺|🇾🇹|🇲🇽|🇫🇲|🇲🇩|🇲🇨|🇲🇳|🇲🇪|🇲🇸|🇲🇦|🇲🇿|🤶🏿|🤶🏻|🤶🏾|🤶🏼|🤶🏽|🇲🇲|🇳🇦|🇳🇷|🇳🇵|🇳🇱|🇳🇨|🇳🇿|🇳🇮|🇳🇪|🇳🇬|🇳🇺|🇳🇫|🇰🇵|🇲🇵|🇳🇴|👌🏿|👌🏻|👌🏾|👌🏼|👌🏽|🇴🇲|🇵🇰|🇵🇼|🇵🇸|🇵🇦|🇵🇬|🇵🇾|🇵🇪|🇵🇭|🇵🇳|🇵🇱|🇵🇹|🇵🇷|🇶🇦|🇷🇴|🇷🇺|🇷🇼|🇷🇪|🇼🇸|🇸🇲|🎅🏿|🎅🏻|🎅🏾|🎅🏼|🎅🏽|🇸🇦|🇸🇳|🇷🇸|🇸🇨|🇸🇱|🇸🇬|🇸🇽|🇸🇰|🇸🇮|🇸🇧|🇸🇴|🇿🇦|🇬🇸|🇰🇷|🇸🇸|🇪🇸|🇱🇰|🇧🇱|🇸🇭|🇰🇳|🇱🇨|🇲🇫|🇵🇲|🇻🇨|🇸🇩|🇸🇷|🇸🇯|🇸🇿|🇸🇪|🇨🇭|🇸🇾|🇸🇹|🇹🇼|🇹🇯|🇹🇿|🇹🇭|🇹🇱|🇹🇬|🇹🇰|🇹🇴|🇹🇹|🇹🇦|🇹🇳|🇹🇷|🇹🇲|🇹🇨|🇹🇻|🇺🇲|🇻🇮|🇺🇬|🇺🇦|🇦🇪|🇬🇧|🇺🇳|🇺🇸|🇺🇾|🇺🇿|🇻🇺|🇻🇦|🇻🇪|🇻🇳|🇼🇫|🇪🇭|🇾🇪|🇿🇲|🇿🇼|🧑🏿|🧑🏻|🧑🏾|🧑🏼|🧑🏽|👼🏿|👼🏻|👼🏾|👼🏼|👼🏽|👶🏿|👶🏻|👶🏾|👶🏼|👶🏽|👇🏿|👇🏻|👇🏾|👇🏼|👇🏽|👈🏿|👈🏻|👈🏾|👈🏼|👈🏽|👉🏿|👉🏻|👉🏾|👉🏼|👉🏽|👆🏿|👆🏻|👆🏾|👆🏼|👆🏽|🧔🏿|🧔🏻|🧔🏾|🧔🏼|🧔🏽|👱🏿|👱🏻|👱🏾|👱🏼|👱🏽|👦🏿|👦🏻|👦🏾|👦🏼|👦🏽|🤱🏿|🤱🏻|🤱🏾|🤱🏼|🤱🏽|👰🏿|👰🏻|👰🏾|👰🏼|👰🏽|🤙🏿|🤙🏻|🤙🏾|🤙🏼|🤙🏽|🧒🏿|🧒🏻|🧒🏾|🧒🏼|🧒🏽|👏🏿|👏🏻|👏🏾|👏🏼|👏🏽|👷🏿|👷🏻|👷🏾|👷🏼|👷🏽|🤞🏿|🤞🏻|🤞🏾|🤞🏼|🤞🏽|🕵🏿|🕵🏻|🕵🏾|🕵🏼|🕵🏽|👂🏿|👂🏻|👂🏾|👂🏼|👂🏽|🧝🏿|🧝🏻|🧝🏾|🧝🏼|🧝🏽|🧚🏿|🧚🏻|🧚🏾|🧚🏼|🧚🏽|💪🏿|💪🏻|💪🏾|💪🏼|💪🏽|🙏🏿|🙏🏻|🙏🏾|🙏🏼|🙏🏽|👧🏿|👧🏻|👧🏾|👧🏼|👧🏽|💂🏿|💂🏻|💂🏾|💂🏼|💂🏽|🖐🏿|🖐🏻|🖐🏾|🖐🏼|🖐🏽|🏇🏿|🏇🏻|🏇🏾|🏇🏼|🏇🏽|☝🏿|☝🏻|☝🏾|☝🏼|☝🏽|🤛🏿|🤛🏻|🤛🏾|🤛🏼|🤛🏽|🤟🏿|🤟🏻|🤟🏾|🤟🏼|🤟🏽|🧙🏿|🧙🏻|🧙🏾|🧙🏼|🧙🏽|🕺🏿|🕺🏻|🕺🏾|🕺🏼|🕺🏽|👨🏿|🕴🏿|🕴🏻|🕴🏾|🕴🏼|🕴🏽|🤵🏿|🤵🏻|🤵🏾|🤵🏼|🤵🏽|👨🏻|👨🏾|👨🏼|👨🏽|👲🏿|👲🏻|👲🏾|👲🏼|👲🏽|🧜🏿|🧜🏻|🧜🏾|🧜🏼|🧜🏽|🖕🏿|🖕🏻|🖕🏾|🖕🏼|🖕🏽|💅🏿|💅🏻|💅🏾|💅🏼|💅🏽|👃🏿|👃🏻|👃🏾|👃🏼|👃🏽|👴🏿|👴🏻|👴🏾|👴🏼|👴🏽|👵🏿|👵🏻|👵🏾|👵🏼|👵🏽|🧓🏿|🧓🏻|🧓🏾|🧓🏼|🧓🏽|👊🏿|👊🏻|👊🏾|👊🏼|👊🏽|👐🏿|👐🏻|👐🏾|👐🏼|👐🏽|🤲🏿|🤲🏻|🤲🏾|🤲🏼|🤲🏽|🚴🏿|🚴🏻|🚴🏾|🚴🏼|🚴🏽|⛹🏿|⛹🏻|⛹🏾|⛹🏼|⛹🏽|🙇🏿|🙇🏻|🙇🏾|🙇🏼|🙇🏽|🤸🏿|🤸🏻|🤸🏾|🤸🏼|🤸🏽|🧗🏿|🧗🏻|🧗🏾|🧗🏼|🧗🏽|🤦🏿|🤦🏻|🤦🏾|🤦🏼|🤦🏽|🙍🏿|🙍🏻|🙍🏾|🙍🏼|🙍🏽|🙅🏿|🙅🏻|🙅🏾|🙅🏼|🙅🏽|🙆🏿|🙆🏻|🙆🏾|🙆🏼|🙆🏽|💇🏿|💇🏻|💇🏾|💇🏼|💇🏽|💆🏿|💆🏻|💆🏾|💆🏼|💆🏽|🏌🏿|🏌🏻|🏌🏾|🏌🏼|🏌🏽|🛌🏿|🛌🏻|🛌🏾|🛌🏼|🛌🏽|🧘🏿|🧘🏻|🧘🏾|🧘🏼|🧘🏽|🧖🏿|🧖🏻|🧖🏾|🧖🏼|🧖🏽|🤹🏿|🤹🏻|🤹🏾|🤹🏼|🤹🏽|🏋🏿|🏋🏻|🏋🏾|🏋🏼|🏋🏽|🚵🏿|🚵🏻|🚵🏾|🚵🏼|🚵🏽|🤾🏿|🤾🏻|🤾🏾|🤾🏼|🤾🏽|🤽🏿|🤽🏻|🤽🏾|🤽🏼|🤽🏽|🙎🏿|🙎🏻|🙎🏾|🙎🏼|🙎🏽|🙋🏿|🙋🏻|🙋🏾|🙋🏼|🙋🏽|🚣🏿|🚣🏻|🚣🏾|🚣🏼|🚣🏽|🏃🏿|🏃🏻|🏃🏾|🏃🏼|🏃🏽|🤷🏿|🤷🏻|🤷🏾|🤷🏼|🤷🏽|🏄🏿|🏄🏻|🏄🏾|🏄🏼|🏄🏽|🏊🏿|🏊🏻|🏊🏾|🏊🏼|🏊🏽|🛀🏿|🛀🏻|🛀🏾|🛀🏼|🛀🏽|💁🏿|💁🏻|💁🏾|💁🏼|💁🏽|🚶🏿|🚶🏻|🚶🏾|🚶🏼|🚶🏽|👳🏿|👳🏻|👳🏾|👳🏼|👳🏽|👮🏿|👮🏻|👮🏾|👮🏼|👮🏽|🤰🏿|🤰🏻|🤰🏾|🤰🏼|🤰🏽|🤴🏿|🤴🏻|🤴🏾|🤴🏼|🤴🏽|👸🏿|👸🏻|👸🏾|👸🏼|👸🏽|🤚🏿|🤚🏻|🤚🏾|🤚🏼|🤚🏽|✊🏿|✊🏻|✊🏾|✊🏼|✊🏽|✋🏿|✋🏻|✋🏾|✋🏼|✋🏽|🙌🏿|🙌🏻|🙌🏾|🙌🏼|🙌🏽|🤜🏿|🤜🏻|🤜🏾|🤜🏼|🤜🏽|🤳🏿|🤳🏻|🤳🏾|🤳🏼|🤳🏽|🤘🏿|🤘🏻|🤘🏾|🤘🏼|🤘🏽|🏂🏿|🏂🏻|🏂🏾|🏂🏼|🏂🏽|👎🏿|👎🏻|👎🏾|👎🏼|👎🏽|👍🏿|👍🏻|👍🏾|👍🏼|👍🏽|🧛🏿|🧛🏻|🧛🏾|🧛🏼|🧛🏽|✌🏿|✌🏻|✌🏾|✌🏼|✌🏽|🖖🏿|🖖🏻|🖖🏾|🖖🏼|🖖🏽|👋🏿|👋🏻|👋🏾|👋🏼|👋🏽|💃🏿|💃🏻|💃🏾|💃🏼|💃🏽|👩🏿|👩🏻|👩🏾|👩🏼|👩🏽|🧕🏿|🧕🏻|🧕🏾|🧕🏼|🧕🏽|✍🏿|✍🏻|✍🏾|✍🏼|✍🏽|🇦🇽|\*⃣|8⃣|5⃣|4⃣|9⃣|1⃣|7⃣|6⃣|3⃣|2⃣|0⃣|\#⃣|🥇|🥈|🥉|🆎|🏧|🅰|♒|♈|🔙|🅱|🆑|🆒|♋|♑|🎄|🔚|🆓|♊|🆔|🉑|🈸|🉐|🏯|㊗|🈹|🎎|🈚|🈁|🈷|🈵|🈶|🈺|🈴|🏣|🈲|🈯|㊙|🈂|🔰|🈳|♌|♎|🤶|🆕|🆖|🆗|👌|🔛|🅾|⛎|🅿|♓|🔜|🆘|♐|🎅|♏|🗽|🦖|🔝|♉|🗼|🆙|🆚|♍|🧮|\U0001fa79|🎟|🧑|🚡|✈|🛬|🛫|⏰|⚗|👽|👾|🚑|🏈|🏺|⚓|💢|😠|👿|😧|🐜|📶|😰|🚛|🎨|😲|⚛|\U0001f6fa|🚗|🥑|\U0001fa93|👶|👼|🍼|🐤|🚼|👇|👈|👉|👆|🥓|🦡|🏸|🥯|🛄|🥖|⚖|🦲|\U0001fa70|🎈|🗳|☑|🍌|\U0001fa95|🏦|📊|💈|⚾|🧺|🏀|🦇|🛁|🔋|🏖|😁|🐻|🧔|💓|🛏|🍺|🔔|🔕|🛎|🍱|\U0001f9c3|🚲|👙|🧢|☣|🐦|🎂|⚫|🏴|🖤|⬛|◾|◼|✒|▪|🔲|👱|🌼|🐡|📘|🔵|💙|\U0001f7e6|🐗|💣|🦴|🔖|📑|📚|🍾|💐|🏹|🥣|🎳|🥊|👦|🧠|🍞|🤱|🧱|👰|🌉|💼|\U0001fa72|🔆|🥦|💔|🧹|\U0001f7e4|\U0001f90e|\U0001f7eb|🐛|🏗|🚅|🌯|🚌|🚏|👤|👥|\U0001f9c8|🦋|🌵|📅|🤙|🐪|📷|📸|🏕|🕯|🍬|🥫|🛶|🗃|📇|🗂|🎠|🎏|🥕|🏰|🐈|🐱|😹|😼|⛓|\U0001fa91|📉|📈|💹|🧀|🏁|🍒|🌸|♟|🌰|🐔|🧒|🚸|🐿|🍫|🥢|⛪|🚬|🎦|Ⓜ|🎪|🏙|🌆|🗜|🎬|👏|🏛|🍻|🥂|📋|🔃|📕|📪|📫|🌂|☁|🌩|⛈|🌧|🌨|🤡|♣|👝|🧥|🍸|🥥|⚰|🥶|💥|☄|🧭|💽|🖱|🎊|😖|😕|🚧|👷|🎛|🏪|🍚|🍪|🍳|©|🛋|🔄|💑|🐄|🐮|🤠|🦀|🖍|💳|🌙|🦗|🏏|🐊|🥐|❌|❎|🤞|🎌|⚔|👑|😿|😢|🔮|🥒|🧁|🥤|🥌|🦱|➰|💱|🍛|🍮|🛃|🥩|🌀|🗡|🍡|💨|\U0001f9cf|🌳|🦌|🚚|🏬|🏚|🏜|🏝|🖥|🕵|♦|💠|🔅|🎯|😞|\U0001f93f|\U0001fa94|💫|😵|🧬|🐕|🐶|💵|🐬|🚪|🔯|➿|‼|🍩|🕊|↙|↘|⬇|😓|🔽|🐉|🐲|👗|🤤|\U0001fa78|💧|🥁|🦆|🥟|📀|📧|🦅|👂|🌽|\U0001f9bb|🥚|🍆|✴|✳|🕣|🕗|⏏|🔌|🐘|🕦|🕚|🧝|✉|📩|💶|🌲|🐑|❗|⁉|🤯|😑|👁|👀|😘|😋|😱|🤮|🤭|🤕|😷|🧐|😮|🤨|🙄|😤|🤬|😂|🤒|😛|😶|🏭|🧚|\U0001f9c6|🍂|👪|⏩|⏬|⏪|⏫|📠|😨|♀|🎡|⛴|🏑|🗄|📁|🎞|📽|🔥|🧯|🧨|🚒|🎆|🌓|🌛|🐟|🍥|🎣|🕠|🕔|⛳|\U0001f9a9|🔦|🥿|⚜|💪|💾|🎴|😳|🥏|🛸|🌫|🌁|🙏|🦶|👣|🍴|🍽|🥠|⛲|🖋|🕟|🍀|🕓|🦊|🖼|🍟|🍤|🐸|🐥|☹|😦|⛽|🌕|🌝|⚱|🎲|\U0001f9c4|⚙|💎|🧞|👻|🦒|👧|🥛|👓|🌎|🌏|🌍|🌐|🧤|🌟|🥅|🐐|👺|🥽|🦍|🎓|🍇|🍏|📗|\U0001f7e2|💚|🥗|\U0001f7e9|😬|😺|😸|😀|😃|😄|😅|😆|💗|💂|\U0001f9ae|🎸|🍔|🔨|⚒|🛠|🐹|🖐|👜|🤝|🐣|🎧|🙉|💟|♥|💘|💝|✔|➗|💲|❣|⭕|➖|✖|➕|🦔|🚁|🌿|🌺|👠|🚄|⚡|🥾|\U0001f6d5|🦛|🕳|🍯|🐝|🚥|🐎|🐴|🏇|🏥|☕|🌭|🥵|🌶|♨|🏨|⌛|⏳|🏠|🏡|🏘|🤗|💯|😯|\U0001f9ca|🍨|🏒|⛸|📥|📨|☝|♾|ℹ|🔤|🔡|🔠|🔢|🔣|🎃|👖|🧩|🃏|🕹|🕋|🦘|🔑|⌨|🔟|🛴|👘|💏|💋|😽|😗|😚|😙|🔪|\U0001fa81|🥝|🐨|🥼|🏷|🥍|🐞|💻|🔷|🔶|🌗|🌜|⏮|✝|🍃|🥬|📒|🤛|↔|⬅|↪|🛅|🗨|🦵|🍋|🐆|🎚|💡|🚈|🔗|🖇|🦁|💄|🚮|🦎|🦙|🦞|🔒|🔐|🔏|🚂|🍭|🧴|😭|📢|🤟|🏩|💌|🧳|🤥|🧙|🧲|🔍|🔎|🀄|♂|👨|👫|🕺|🕴|🤵|👲|🥭|🕰|\U0001f9bd|👞|🗾|🍁|🥋|\U0001f9c9|🍖|\U0001f9be|\U0001f9bf|⚕|📣|🍈|📝|🕎|🚹|🧜|🚇|🦠|🎤|🔬|🖕|🎖|🌌|🚐|🗿|📱|📴|📲|🤑|💰|💸|🐒|🐵|🚝|🥮|🎑|🕌|🦟|🛥|🛵|🏍|\U0001f9bc|🛣|🗻|⛰|🚠|🚞|🐁|🐭|👄|🎥|🍄|🎹|🎵|🎶|🎼|🔇|💅|📛|🏞|🤢|🧿|👔|🤓|😐|🌑|🌚|📰|⏭|🌃|🕤|🕘|🚳|⛔|🚯|📵|🔞|🚷|🚭|🚱|👃|📓|📔|🔩|🐙|🍢|🏢|👹|🛢|🗝|👴|👵|🧓|🕉|🚘|🚍|👊|🚔|🚖|\U0001fa71|🕜|🕐|\U0001f9c5|📖|📂|👐|📭|📬|💿|📙|\U0001f7e0|🧡|\U0001f7e7|\U0001f9a7|☦|\U0001f9a6|📤|🦉|🐂|\U0001f9aa|📦|📄|📃|📟|🖌|🌴|🤲|🥞|🐼|📎|🦜|〽|🎉|🥳|🛳|🛂|⏸|🐾|☮|🍑|🦚|🥜|🍐|🖊|✏|🐧|😔|👯|🤼|🎭|😣|🚴|⛹|🙇|🤸|🧗|🤦|🤺|🙍|🙅|🙆|💇|💆|🏌|🛌|🧘|🧖|🤹|\U0001f9ce|🏋|🚵|🤾|🤽|🙎|🙋|🚣|🏃|🤷|\U0001f9cd|🏄|🏊|🛀|💁|🚶|👳|🧫|⛏|🥧|🐖|🐷|🐽|💩|💊|\U0001f90f|🎍|🍍|🏓|🔫|🍕|🛐|▶|⏯|🥺|🚓|🚨|👮|🐩|🎱|🍿|🏤|📯|📮|🍲|🚰|🥔|🍗|💷|😾|😡|📿|🤰|🥨|\U0001f9af|🤴|👸|🖨|🚫|\U0001f7e3|💜|\U0001f7ea|👛|📌|❓|🐇|🐰|🦝|🏎|📻|🔘|☢|🚃|🛤|🌈|🤚|✊|✋|🙌|🐏|🐀|\U0001fa92|\U0001fa90|🧾|⏺|♻|🍎|🔴|🧧|🦰|❤|🏮|\U0001f7e5|🔻|🔺|®|😌|🎗|🔁|🔂|⛑|🚻|◀|💞|🦏|🎀|🍙|🍘|🤜|🗯|➡|⤵|↩|⤴|💍|🍠|🤖|🚀|🧻|🗞|🎢|🤣|🐓|🌹|🏵|📍|🏉|🎽|👟|😥|🧷|\U0001f9ba|🧂|⛵|🍶|🥪|\U0001f97b|🛰|📡|🦕|🎷|🧣|🏫|🎒|✂|🦂|📜|💺|🙈|🌱|🤳|🕢|🕖|🥘|☘|🦈|🍧|🌾|🛡|⛩|🚢|🌠|🛍|🛒|🍰|\U0001fa73|🚿|🦐|🔀|🤫|🤘|🕡|🕕|🛹|⛷|🎿|💀|☠|\U0001f9a8|🛷|😴|😪|🙁|🙂|🎰|\U0001f9a5|🛩|🔹|🔸|😻|☺|😇|🥰|😍|😈|😊|😎|😏|🐌|🐍|🤧|🏔|🏂|❄|☃|⛄|🧼|⚽|🧦|🥎|🍦|♠|🍝|❇|🎇|✨|💖|🙊|🔊|🔈|🔉|🗣|💬|🚤|🕷|🕸|🗓|🗒|🐚|🥄|🧽|🚙|🏅|🐳|🦑|😝|🏟|🤩|☪|✡|🚉|🍜|\U0001fa7a|⏹|🛑|⏱|📏|🍓|🎙|🥙|☀|⛅|🌥|🌦|🌤|🌞|🌻|🕶|🌅|🌄|🌇|🦸|🦹|🍣|🚟|🦢|💦|🕍|💉|👕|🌮|🥡|🎋|🍊|🚕|🍵|📆|🧸|☎|📞|🔭|📺|🕥|🕙|🎾|⛺|🧪|🌡|🤔|💭|🧵|🕞|🕒|👎|👍|🎫|🐅|🐯|⏲|😫|🧰|🚽|🍅|👅|🦷|🎩|🌪|🖲|🚜|™|🚆|🚊|🚋|🚩|📐|🔱|🚎|🏆|🍹|🐠|🎺|🌷|🥃|🦃|🐢|🕧|🕛|🐫|🕝|💕|👬|🕑|👭|☂|⛱|☔|😒|🦄|🔓|↕|↖|↗|⬆|🙃|🔼|🧛|🚦|📳|✌|📹|🎮|📼|🎻|🌋|🏐|🖖|\U0001f9c7|🌘|🌖|⚠|🗑|⌚|🐃|🚾|🌊|🍉|👋|〰|🌒|🌔|🙀|😩|💒|🐋|☸|♿|⚪|❕|🏳|💮|🦳|\U0001f90d|✅|⬜|◽|◻|⭐|❔|▫|🔳|🥀|🎐|🌬|🍷|😉|😜|🐺|👩|💃|🧕|👢|👚|👒|👡|🚺|🥴|🗺|😟|🎁|🔧|✍|🧶|\U0001f971|\U0001f7e1|💛|\U0001f7e8|💴|\U0001fa80|☯|🤪|🦓|🤐|🧟|💤|🏻|🏼|🏽|🏾|🏿|🇦|🇧|🇨|🇩|🇪|🇫|🇬|🇭|🇮|🇯|🇰|🇱|🇲|🇳|🇴|🇵|🇶|🇷|🇸|🇹|🇺|🇻|🇼|🇽|🇾|🇿' ]|^'|'$|''"
)


def is_date_str(var) -> bool:
    try:
        datetime.strptime(str(var), "%Y-%m-%d")
    except ValueError:
        # raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return False
    return True


def is_datetime_str(var) -> bool:
    try:
        datetime.strptime(str(var), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return False
    return True


def is_number_str(var) -> bool:
    if RE_NUM.fullmatch(str(var)):
        return True
    return False


def is_latin_str(var) -> bool:
    if RE_LATIN.fullmatch(str(var)):
        return True
    return False


def is_thai_str(var) -> bool:
    if RE_THAI.fullmatch(str(var)):
        return True
    return False


def replace_text(text: str, replace_pairs: Iterable[Tuple[str, str]]) -> str:
    # consider using str.translate
    for k, v in replace_pairs:
        text = text.replace(k, v)
    return text


def normalize_text_pairs(text: str) -> str:
    return replace_text(text, COMBINED_NORMALIZE_PAIRS)


def normalize_link(text: str, place_holder: str = REPLACE_LINK) -> str:
    text = RE_HTTP_WWW.sub(place_holder, text)  # http, https, mailto, www.
    text = RE_EXT.sub(place_holder, text)  # .html, php3, .jpg
    return text


def normalize_at_mention(text: str, place_holder: str = REPLACE_AT_MENTION) -> str:
    text = RE_AT_MENTION.sub(place_holder, text)  # @mention
    return text


def normalize_email(text: str, place_holder: str = REPLACE_EMAIL) -> str:
    text = RE_EMAIL.sub(place_holder, text)  # mail@address.com
    return text


def normalize_haha(text: str, place_holder: str = REPLACE_HAHA) -> str:
    text = RE_HAHA.sub(place_holder, text)
    return text


def normalize_num(text: str, place_holder: str = REPLACE_NUMBER) -> str:
    text = RE_NUM.sub(place_holder, text)  # any number that longer than 2 digits
    return text


def normalize_phone(text: str, place_holder: str = REPLACE_PHONE) -> str:
    text = RE_PHONE.sub(place_holder, text)
    return text


def normalize_accented_chars(text: str) -> str:
    return replace_text(text, ACCENTED_PAIRS)


def normalize_special_chars(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("utf-8", errors="ignore")
        .decode("utf-8")
    )


def remove_hashtags(text: str) -> str:
    return RE_HASHTAGS.sub("", text)


def remove_tag(text: str) -> str:
    """
    Remove markup tags using regular expression.
    For more sophisticated HTML/XML tags removal, consider using libraries
    like xml.etree or BeautifulSoup (heavier weight).
    """
    text = RE_TAG.sub("", text)
    return text


# def remove_dup_chars(text: str) -> str:
#     """
#     Replace duplicated characters
#     e.g.
#     righttttt -> rightttt
#     มรรรรรค -> มรรรรค
#     มาาาาาาาาาาาาาาาาาาาาาาากกกก -> มากกกก
#     อิอิอิอิอิอิ -> อิอิอิอิ
#     ! ! ! ! -> !
#     """
#     text = RE_DUP_C_C.sub(r"\1", text)
#     text = RE_DUP_CC.sub(r"\1\1", text)
#     text = RE_DUP_C6.sub(r"\1\1\1\1\1", text)
#     text = RE_DUP_THAI.sub(r"\1", text)
#     return text


# " ".join(text.split()) will remove newlines, which we may like to preserve them
def remove_dup_spaces(text: str) -> str:
    text = RE_DUP_SPACE.sub(" ", text)
    text = RE_DUP_EMPTYLINE.sub("\n", text)
    text = RE_STRIP.sub("", text)
    return text.strip()


def insert_spaces(text: str) -> str:
    text = RE_DIGIT_NONDIGIT.sub(r"\1 \2", text)  # (Digit)(Non-digit)
    text = RE_NONDIGIT_DIGIT.sub(r"\1 \2", text)  # (Non-Digit)(Digit)
    text = RE_THAI_NONTHAI.sub(r"\1 \2", text)  # (Thai)(Non-Thai)
    text = RE_NONTHAI_THAI.sub(r"\1 \2", text)  # (Non-Thai)(Thai)
    text = RE_LATIN_NONLATIN.sub(r"\1 \2", text)  # (Latin)(Non-Latin)
    text = RE_NONLATIN_LATIN.sub(r"\1 \2", text)  # (Non-Latin)(Latin)

    return text


def remove_emoji(text: str) -> str:
    return RE_EMOJI.sub("", text)


def normalize_emoji(text: str) -> str:
    return re.sub(RE_EMOJI, r" \1 ", text).strip()


def remove_others_char(text):
    text = re.sub(RE_NONTHAI_ENG_EMOJI, " ", text)
    return text


def replace_rep_after(text: str) -> str:
    def _replace_rep(m):
        c, _ = m.groups()
        return f"{c}"

    re_rep = re.compile(r"(\S)(\1{2,})")

    return re_rep.sub(_replace_rep, text)


# The current sequence of operations is designed to produce text
# to be a training data for classification task.
def preprocess(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    text = html.unescape(text)
    text = remove_tag(text)

    text = normalize_link(text)
    text = normalize_at_mention(text)
    text = normalize_email(text)
    text = normalize_phone(text)
    text = normalize_text_pairs(text)
    text = normalize_haha(text)
    text = normalize_num(text)
    text = normalize_emoji(text)

    text = remove_others_char(text)

    text = insert_spaces(text)
    text = remove_dup_spaces(text)

    return text


def remove_stopwords(
    tokens: list, custom_stopwords: list = [], include_legacy_stopwords: bool = True
) -> list:
    stopwords = list(THAI_STOPWORDS)
    if custom_stopwords:
        if include_legacy_stopwords:
            stopwords += custom_stopwords
        else:
            stopwords = custom_stopwords
    return [token for token in tokens if token not in stopwords]
