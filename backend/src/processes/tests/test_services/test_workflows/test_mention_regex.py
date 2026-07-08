"""
Unit tests for MENTION_RE regex pattern.

Pure unit tests — no database required.
"""

from src.processes.services.workflow_permissions import MENTION_RE


def test_mention_re__single__returns_id():
    # arrange
    text = 'Hey [John Doe| 42] check this'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['42']


def test_mention_re__multiple__returns_all():
    # arrange
    text = '[Alice| 1] and [Bob| 2] please review'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert set(result) == {'1', '2'}


def test_mention_re__no_mention__empty():
    # arrange
    text = 'Just a regular comment with no mentions'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == []


def test_mention_re__no_space__returns_id():
    # arrange
    text = '[Name|99] no space before id'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['99']


def test_mention_re__extra_spaces__returns_id():
    # arrange
    text = '[Name|   777] extra spaces'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['777']


def test_mention_re__special_chars_in_name__ok():
    # arrange
    text = '[John (Admin)|123] special chars in name'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['123']


def test_mention_re__empty_brackets__no_match():
    # arrange
    text = '[]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == []


def test_mention_re__pipe_only__no_match():
    # arrange
    text = '[Name|]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == []


def test_mention_re__name_with_pipe__last_segment():
    # arrange
    text = '[Name|Title| 42]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['42']


def test_mention_re__newline_between__both():
    # arrange
    text = 'Line 1 [A| 1]\nLine 2 [B| 2]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert set(result) == {'1', '2'}


def test_mention_re__zero_id__captured():
    # arrange
    text = '[User| 0]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['0']


def test_mention_re__large_id__captured():
    # arrange
    text = '[User| 999999999]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['999999999']


def test_mention_re__adjacent__both_captured():
    # arrange
    text = '[A| 1][B| 2]'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert set(result) == {'1', '2'}


def test_mention_re__inside_quotes__captured():
    # arrange
    text = '"[User| 42]" is mentioned'

    # act
    result = MENTION_RE.findall(text)

    # assert
    assert result == ['42']
