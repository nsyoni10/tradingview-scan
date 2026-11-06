"""Build the PROTFOLIO HTML dashboard from a TradingView data snapshot.

Usage: python portfolio/build_html.py portfolio/data_YYYY-MM-DD.json YYYY-MM-DD
Output: portfolio/portfolio_YYYY-MM-DD.html

The watchlist order (including ### section headers) is kept in ORDER below and
should be refreshed from the TradingView watchlist "PROTFOLIO" (id 333478269).
"""
import json
import pathlib
import sys

ORDER = ["NASDAQ:QQQ", "AMEX:SPY", "TVC:USOIL", "TVC:VIX", "###פעילים", "NYSE:VOYA", "NASDAQ:WMG", "NYSE:GME",
         "NYSE:BNY", "NYSE:DIS", "NASDAQ:DASH", "NASDAQ:NBIX", "NYSE:LEN", "###במעקב", "NYSE:TGT", "NYSE:IR",
         "NYSE:GD", "NYSE:BR", "NASDAQ:CTSH", "NYSE:NET", "NASDAQ:BBIO", "NASDAQ:AVT", "NYSE:BEN", "NYSE:EMBJ",
         "NYSE:SNOW", "NASDAQ:TEM", "NASDAQ:CBRS", "###לקחת", "NASDAQ:ARCC", "NYSE:NRP", "NYSE:OWL", "NASDAQ:MNST",
         "NASDAQ:GOOGL", "NASDAQ:MSTR", "###לקחת מעט מתןחים"]

here = pathlib.Path(__file__).parent
data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
date = sys.argv[2]
html = (here / "template.html").read_text(encoding="utf-8")
html = (html.replace("__ORDER__", json.dumps(ORDER, ensure_ascii=False))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__DATE__", date))
out = here / f"portfolio_{date}.html"
out.write_text(html, encoding="utf-8")
print(out)
