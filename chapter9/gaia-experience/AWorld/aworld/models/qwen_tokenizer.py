# Copyright 2023 The Qwen team, Alibaba Group. All rights reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tokenization classes for QWen."""

import base64
import unicodedata
from pathlib import Path
from typing import Collection, Dict, List, Set, Union
from aworld.logs.util import logger
from aworld.utils import import_package
import_package("tiktoken")
import tiktoken

VOCAB_FILES_NAMES = {'vocab_file': 'qwen.tiktoken'}

PAT_STR = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
ENDOFTEXT = '<|endoftext|>'
IMSTART = '<|im_start|>'
IMEND = '<|im_end|>'
# as the default behavior is changed to allow special tokens in
# regular texts, the surface forms of special tokens need to be
# as different as possible to minimize the impact
EXTRAS = tuple((f'<|extra_{i}|>' for i in range(205)))
# changed to use actual index to avoid misconfiguration with vocabulary expansion
SPECIAL_START_ID = 151643
SPECIAL_TOKENS = tuple(enumerate(
    ((
        ENDOFTEXT,
        IMSTART,
        IMEND,
    ) + EXTRAS),
    start=SPECIAL_START_ID,
))
SPECIAL_TOKENS_SET = set(t for i, t in SPECIAL_TOKENS)


def _load_tiktoken_bpe(tiktoken_bpe_file: str) -> Dict[bytes, int]:
    with open(tiktoken_bpe_file, 'rb') as f:
        contents = f.read()
    return {
        base64.b64decode(token): int(rank) for token, rank in (line.split() for line in contents.splitlines() if line)
    }


class QWenTokenizer:
    """QWen tokenizer."""

    vocab_files_names = VOCAB_FILES_NAMES

    def __init__(
        self,
        vocab_file=None,
        errors='replace',
        extra_vocab_file=None,
    ):
        if not vocab_file:
            vocab_file = VOCAB_FILES_NAMES['vocab_file']
        self._decode_use_source_tokenizer = False

        # how to handle errors in decoding UTF-8 byte sequences
        # use ignore if you are in streaming inference
        self.errors = errors

        self.mergeable_ranks = _load_tiktoken_bpe(vocab_file)  # type: Dict[bytes, int]
        self.special_tokens = {token: index for index, token in SPECIAL_TOKENS}

        # try load extra vocab from file
        if extra_vocab_file is not None:
            used_ids = set(self.mergeable_ranks.values()) | set(self.special_tokens.values())
            extra_mergeable_ranks = _load_tiktoken_bpe(extra_vocab_file)
            for token, index in extra_mergeable_ranks.items():
                if token in self.mergeable_ranks:
                    logger.info(f'extra token {token} exists, skipping')
                    continue
                if index in used_ids:
                    logger.info(f'the index {index} for extra token {token} exists, skipping')
                    continue
                self.mergeable_ranks[token] = index
            # the index may be sparse after this, but don't worry tiktoken.Encoding will handle this

        enc = tiktoken.Encoding(
            'Qwen',
            pat_str=PAT_STR,
            mergeable_ranks=self.mergeable_ranks,
            special_tokens=self.special_tokens,
        )
        assert len(self.mergeable_ranks) + len(
            self.special_tokens
        ) == enc.n_vocab, f'{len(self.mergeable_ranks) + len(self.special_tokens)} != {enc.n_vocab} in encoding'

        self.decoder = {v: k for k, v in self.mergeable_ranks.items()}  # type: dict[int, bytes|str]
        self.decoder.update({v: k for k, v in self.special_tokens.items()})

        self.tokenizer = enc  # type: tiktoken.Encoding

        self.eod_id = self.tokenizer.eot_token
        self.im_start_id = self.special_tokens[IMSTART]
        self.im_end_id = self.special_tokens[IMEND]

    def __getstate__(self):
        # for pickle lovers
        state = self.__dict__.copy()
        del state['tokenizer']
        return state

    def __setstate__(self, state):
        # tokenizer is not python native; don't pass it; rebuild it
        self.__dict__.update(state)
        enc = tiktoken.Encoding(
            'Qwen',
            pat_str=PAT_STR,
            mergeable_ranks=self.mergeable_ranks,
            special_tokens=self.special_tokens,
        )
        self.tokenizer = enc

    def __len__(self) -> int:
        return self.tokenizer.n_vocab

    def get_vocab(self) -> Dict[bytes, int]:
        return self.mergeable_ranks

    def convert_tokens_to_ids(self, tokens: Union[bytes, str, List[Union[bytes, str]]]) -> List[int]:
        ids = []
        if isinstance(tokens, (str, bytes)):
            if tokens in self.special_tokens:
                return self.special_tokens[tokens]
            else:
                return self.mergeable_ranks.get(tokens)
        for token in tokens:
            if token in self.special_tokens:
                ids.append(self.special_tokens[token])
            else:
                ids.append(self.mergeable_ranks.get(token))
        return ids

    def tokenize(
            self,
            text: str,
            allowed_special: Union[Set, str] = 'all',
            disallowed_special: Union[Collection, str] = (),
    ) -> List[Union[bytes, str]]:
        """
        Converts a string in a sequence of tokens.

        Args:
            text (`str`):
                The sequence to be encoded.
            allowed_special (`Literal["all"]` or `set`):
                The surface forms of the tokens to be encoded as special tokens in regular texts.
                Default to "all".
            disallowed_special (`Literal["all"]` or `Collection`):
                The surface forms of the tokens that should not be in regular texts and trigger errors.
                Default to an empty tuple.

        Returns:
            `List[bytes|str]`: The list of tokens.
        """
        tokens = []
        if text is None:
            return tokens
        text = unicodedata.normalize('NFC', text)

        # this implementation takes a detour: text -> token id -> token surface forms
        for t in self.tokenizer.encode(text, allowed_special=allowed_special, disallowed_special=disallowed_special):
            tokens.append(self.decoder[t])
        return tokens

    def convert_tokens_to_string(self, tokens: List[Union[bytes, str]]) -> str:
        """
        Converts a sequence of tokens in a single string.
        """
        text = ''
        temp = b''
        for t in tokens:
            if isinstance(t, str):
                if temp:
                    text += temp.decode('utf-8', errors=self.errors)
                    temp = b''
                text += t
            elif isinstance(t, bytes):
                temp += t
            else:
                raise TypeError('token should only be of type types or str')
        if temp:
            text += temp.decode('utf-8', errors=self.errors)
        return text

    @property
    def vocab_size(self):
        return self.tokenizer.n_vocab

    def _decode(
        self,
        token_ids: Union[int, List[int]],
        skip_special_tokens: bool = False,
        errors: str = None,
    ) -> str:
        if isinstance(token_ids, int):
            token_ids = [token_ids]
        if skip_special_tokens:
            token_ids = [i for i in token_ids if i < self.eod_id]
        return self.tokenizer.decode(token_ids, errors=errors or self.errors)

    def encode(self, text: str) -> List[int]:
        return self.convert_tokens_to_ids(self.tokenize(text))

    def count_tokens(self, text: str) -> int:
        return len(self.tokenize(text))

    def truncate(self, text: str, max_token: int, start_token: int = 0, keep_both_sides: bool = False) -> str:
        max_token = int(max_token)
        token_list = self.tokenize(text)[start_token:]
        if len(token_list) <= max_token:
            return self.convert_tokens_to_string(token_list)

        if keep_both_sides:
            ellipsis_tokens = self.tokenize("...")
            ellipsis_len = len(ellipsis_tokens)
            available = max_token - ellipsis_len
            if available <= 0: # Degenerate case: not enough space even for "..."
                return self.convert_tokens_to_string(token_list[:max_token])

            left_len = available // 2
            right_len = available - left_len
            token_list = token_list[:left_len] + ellipsis_tokens + token_list[-right_len:]
        else:
            token_list = token_list[:max_token]

        return self.convert_tokens_to_string(token_list)


qwen_tokenizer = QWenTokenizer(Path(__file__).resolve().parent.parent / 'config' / 'qwen.tiktoken')
