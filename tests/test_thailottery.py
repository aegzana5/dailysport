from unittest.mock import Mock, patch

from fetchers.thailottery import (
    _collect_thaiorc_results,
    _page_url,
    _parse_thaiorc_results,
    _thaiorc_date_to_iso,
    fetch_results,
)


def _thaiorc_fixture() -> str:
    return """
    <tr>
    <td width="34%" class="bd-bgray bd-lgray bd-rgray pd-t8 pd-b10 stats-title" align="center"><a class="blue-nl16" href="../../../lotto/thai/jackpot.php?contentID=25690502">02/05/2569</a></td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">536077</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center">077</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">77</td>
    </tr><tr>
    <td width="34%" class="bd-bgray bd-lgray bd-rgray pd-t8 pd-b10 stats-title" align="center"><a class="blue-nl16" href="../../../lotto/thai/jackpot.php?contentID=25690416">16/04/2569</a></td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">309612</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center">612</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">12</td>
    </tr><tr>
    <td width="34%" class="bd-bgray bd-lgray bd-rgray pd-t8 pd-b10 stats-title" align="center"><a class="blue-nl16" href="../../../lotto/thai/jackpot.php?contentID=25690401">01/04/2569</a></td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">292514</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center">514</td>
    <td width="22%" class="bd-bgray bd-rgray pd-t8 pd-b10 stats-title" align="center" bgcolor="#f1f4f5">14</td>
    </tr>
    """.strip()


def test_thaiorc_date_to_iso_converts_buddhist_year():
    assert _thaiorc_date_to_iso("02", "05", "2569") == "2026-05-02"


def test_parse_thaiorc_results_returns_lottery_rows():
    assert _parse_thaiorc_results(_thaiorc_fixture()) == [
        {"date": "2026-05-02", "prize1": "536077", "two_digit": "77"},
        {"date": "2026-04-16", "prize1": "309612", "two_digit": "12"},
        {"date": "2026-04-01", "prize1": "292514", "two_digit": "14"},
    ]


def test_parse_thaiorc_results_empty_html():
    assert _parse_thaiorc_results("<html></html>") == []


def test_page_url_uses_pagination_after_page_one():
    assert _page_url(1) == "https://horoscope.thaiorc.com/lotto/thai/stats/lottery-years10.php"
    assert _page_url(2) == "https://horoscope.thaiorc.com/lotto/thai/stats/lottery-years10.php?pg=2"


def test_collect_thaiorc_results_walks_pages_and_stops_at_limit():
    page1 = Mock(text=_thaiorc_fixture(), apparent_encoding="cp874")
    page1.raise_for_status = Mock()
    page1.encoding = None
    page2 = Mock(
        text="""
        <tr>
        <td><a href="../../../lotto/thai/jackpot.php?contentID=25690316">16/03/2569</a></td>
        <td>123456</td><td>456</td><td>56</td>
        </tr><tr>
        <td><a href="../../../lotto/thai/jackpot.php?contentID=25690301">01/03/2569</a></td>
        <td>654321</td><td>321</td><td>21</td>
        </tr>
        """.strip(),
        apparent_encoding="cp874",
    )
    page2.raise_for_status = Mock()
    page2.encoding = None
    with patch("fetchers.thailottery.requests.get", side_effect=[page1, page2]) as mock_get:
        results = _collect_thaiorc_results(limit=4)
    assert [r["date"] for r in results] == ["2026-05-02", "2026-04-16", "2026-04-01", "2026-03-16"]
    assert mock_get.call_args_list[0].args == ("https://horoscope.thaiorc.com/lotto/thai/stats/lottery-years10.php",)
    assert mock_get.call_args_list[1].args == ("https://horoscope.thaiorc.com/lotto/thai/stats/lottery-years10.php?pg=2",)


def test_collect_thaiorc_results_stops_on_empty_page():
    page1 = Mock(text=_thaiorc_fixture(), apparent_encoding="cp874")
    page1.raise_for_status = Mock()
    page1.encoding = None
    page2 = Mock(text="<html></html>", apparent_encoding="cp874")
    page2.raise_for_status = Mock()
    page2.encoding = None
    with patch("fetchers.thailottery.requests.get", side_effect=[page1, page2]) as mock_get:
        results = _collect_thaiorc_results(limit=100)
    assert len(results) == 3
    assert mock_get.call_count == 2


def test_fetch_results_uses_100_draw_collector():
    with patch("fetchers.thailottery._collect_thaiorc_results", return_value=[{"date": "2026-05-02", "prize1": "536077", "two_digit": "77"}]) as mock_collect:
        results = fetch_results()
    mock_collect.assert_called_once_with(limit=100)
    assert results[0]["prize1"] == "536077"


def test_fetch_results_returns_empty_on_exception():
    with patch("fetchers.thailottery._collect_thaiorc_results", side_effect=Exception("network error")):
        results = fetch_results()
    assert results == []
