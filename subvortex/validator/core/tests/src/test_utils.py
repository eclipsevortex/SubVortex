# The MIT License (MIT)
# Copyright © 2025 Eclipse Vortex

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from types import SimpleNamespace
from subvortex.validator.core.challenger.utils import apply_sma

def test_apply_sma_challenge_period_1():
    settings = SimpleNamespace(challenge_period=1)
    result = apply_sma(settings, [], score=0.9, default_score=0.0)
    assert result == [0.9]

    result = apply_sma(settings, [0.5], score=0.9, default_score=0.0)
    assert result == [0.9]

    result = apply_sma(settings, [0.5, 0.6], score=0.9, default_score=0.0)
    assert result == [0.9]

def test_apply_sma_short_padding():
    settings = SimpleNamespace(challenge_period=3)
    result = apply_sma(settings, [], score=1.0, default_score=0.0)
    assert result == [0.0, 0.0, 1.0]

    result = apply_sma(settings, [0.5], score=1.0, default_score=0.0)
    assert result == [0.0, 0.5, 1.0]

    result = apply_sma(settings, [0.3, 0.4], score=1.0, default_score=0.0)
    assert result == [0.3, 0.4, 1.0]

def test_apply_sma_exact_length_scores():
    settings = SimpleNamespace(challenge_period=4)
    result = apply_sma(settings, [0.1, 0.2, 0.3], score=0.4, default_score=0.0)
    assert result == [0.1, 0.2, 0.3, 0.4]

def test_apply_sma_exceeds_period():
    settings = SimpleNamespace(challenge_period=3)
    result = apply_sma(settings, [0.1, 0.2, 0.3, 0.4], score=0.5, default_score=0.0)
    # expect last challenge_period-1 = 2 elements: 0.3, 0.4 + new score
    assert result == [0.3, 0.4, 0.5]

def test_apply_sma_all_defaults_then_score():
    settings = SimpleNamespace(challenge_period=5)
    result = apply_sma(settings, [], score=0.8, default_score=1.0)
    assert result == [1.0, 1.0, 1.0, 1.0, 0.8]

def test_apply_sma_int_float_mix():
    settings = SimpleNamespace(challenge_period=4)
    result = apply_sma(settings, [1, 2.0], score=3, default_score=0)
    assert result == [0, 1, 2.0, 3]

def test_apply_sma_with_negatives():
    settings = SimpleNamespace(challenge_period=4)
    result = apply_sma(settings, [-1, -0.5, 0.0], score=0.5, default_score=0)
    assert result == [-1, -0.5, 0.0, 0.5]
