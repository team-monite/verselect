import re

import pytest

from verselect.assembly.responses import set_allowed_responses


def test__set_allowed_responses():
    set_allowed_responses(codes=[200])
    set_allowed_responses(codes={409: "11"})
    with pytest.raises(TypeError, match=re.escape("codes should be `list` or `dict`, found: <class 'str'>")):
        set_allowed_responses(codes="fefe")  # pyright: ignore[reportGeneralTypeIssues]


if __name__ == "__main__":
    pass
