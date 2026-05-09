from unittest.mock import Mock, patch

from fetchers.laolottery import (
    _collect_thaiorc_results,
    _page_url,
    _parse_thaiorc_results,
    _thaiorc_date_to_iso,
    fetch_results,
)

def _thaiorc_fixture() -> str:
    return """
    <tr>
    <td width="34%" class="bd-bgray bd-lgray bd-rgray pd-t8 pd-b10 stats-title" align="center"><a class="blue-nl16" href="../../../lotto/lao/jackpot.php?contentID=25690505">05/05/2569</a></td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">7032</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center">032</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">32</td>
    </tr><tr>
    <td width="34%" class="bd-bgray bd-lgray bd-rgray pd-t8 pd-b10 stats-title" align="center"><a class="blue-nl16" href="../../../lotto/lao/jackpot.php?contentID=25690504">04/05/2569</a></td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">9193</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center">193</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">93</td>
    </tr><tr>
    <td width="34%" class="bd-bgray bd-lgray bd-rgray pd-t8 pd-b10 stats-title" align="center"><a class="blue-nl16" href="../../../lotto/lao/jackpot.php?contentID=25690404">04/04/2569</a></td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">2222</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center">222</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">22</td>
    </tr>
    """.strip()


def test_thaiorc_date_to_iso_converts_buddhist_year():
    assert _thaiorc_date_to_iso("05", "05", "2569") == "2026-05-05"


def test_parse_thaiorc_results_returns_lottery_rows():
    assert _parse_thaiorc_results(_thaiorc_fixture()) == [
        {"date": "2026-05-05", "time": "", "number": "7032", "two_digit": "70", "upper_two_digit": "32"},
        {"date": "2026-05-04", "time": "", "number": "9193", "two_digit": "91", "upper_two_digit": "93"},
        {"date": "2026-04-04", "time": "", "number": "2222", "two_digit": "22", "upper_two_digit": "22"},
    ]


def test_page_url_uses_pagination_after_page_one():
    assert _page_url(1) == "https://horoscope.thaiorc.com/lotto/lao/stats/lottery-years10.php"
    assert _page_url(2) == "https://horoscope.thaiorc.com/lotto/lao/stats/lottery-years10.php?pg=2"


def test_collect_thaiorc_results_walks_pages_and_stops_at_limit():
    page1 = Mock(text=_thaiorc_fixture(), apparent_encoding="cp874")
    page1.raise_for_status = Mock()
    page1.encoding = None
    page2 = Mock(
        text="""
        <tr>
        <td><a href="../../../lotto/lao/jackpot.php?contentID=25690403">03/04/2569</a></td>
        <td>3333</td><td>333</td><td>33</td>
        </tr><tr>
        <td><a href="../../../lotto/lao/jackpot.php?contentID=25690402">02/04/2569</a></td>
        <td>4444</td><td>444</td><td>44</td>
        </tr>
        """.strip(),
        apparent_encoding="cp874",
    )
    page2.raise_for_status = Mock()
    page2.encoding = None
    with patch("fetchers.laolottery.requests.get", side_effect=[page1, page2]) as mock_get:
        results = _collect_thaiorc_results(limit=4)
    assert [item["date"] for item in results] == ["2026-05-05", "2026-05-04", "2026-04-04", "2026-04-03"]
    assert mock_get.call_args_list[0].args == ("https://horoscope.thaiorc.com/lotto/lao/stats/lottery-years10.php",)
    assert mock_get.call_args_list[1].args == ("https://horoscope.thaiorc.com/lotto/lao/stats/lottery-years10.php?pg=2",)


def test_fetch_results_uses_100_draw_collector():
    with patch("fetchers.laolottery._collect_thaiorc_results", return_value=[{"date": "2026-05-05", "time": "", "number": "7032", "two_digit": "70", "upper_two_digit": "32"}]) as mock_collect:
        results = fetch_results()
    mock_collect.assert_called_once_with(limit=100)
    assert results[0]["number"] == "7032"
