import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
from pipeline.validate_ncs_matching import normalize_ncs_code

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2020302.0", "02020302"),
        ("13010102.0", "13010102"),
        ("ABC", "ABC"),
        ("123456789", "123456789"),
        (None, None),
        ("  00123.0  ", "0000123"),
        ("0", "00000000"),
    ]
)
def test_normalize_ncs_code(raw, expected):
    assert normalize_ncs_code(raw) == expected
