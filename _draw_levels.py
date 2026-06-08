import json, asyncio, websockets, time

CDP_URL = "http://localhost:9222"

def get_chart_page():
    import urllib.request
    with urllib.request.urlopen(f"{CDP_URL}/json") as r:
        pages = json.loads(r.read())
    for p in pages:
        if 'tradingview' in p.get('url', ''):
            return p['webSocketDebuggerUrl']
    raise RuntimeError("TradingView chart page not found")

async def send_cmd(ws, method, params=None, cmd_id=1):
    msg = json.dumps({"id": cmd_id, "method": method, "params": params or {}})
    await ws.send(msg)
    while True:
        resp = json.loads(await ws.recv())
        if resp.get('id') == cmd_id:
            return resp

async def eval_js(ws, js, cmd_id=1):
    r = await send_cmd(ws, "Runtime.evaluate", {
        "expression": js,
        "awaitPromise": True,
        "timeout": 15000
    }, cmd_id)
    return r

async def navigate_to(ws, symbol, cmd_id):
    js = f"""
(async () => {{
    const widget = window.tvWidget || Object.values(window).find(v => v && v.chart && typeof v.chart === 'function');
    if (!widget) return 'no_widget';
    widget.setSymbol('{symbol}', '1D', () => {{}});
    await new Promise(r => setTimeout(r, 3500));
    return 'navigated';
}})()
"""
    r = await eval_js(ws, js, cmd_id)
    return r.get('result', {}).get('result', {}).get('value', 'unknown')

async def draw_levels(ws, symbol, levels, cmd_id):
    lines_js = json.dumps(levels)
    js = f"""
(async () => {{
    await new Promise(r => setTimeout(r, 1000));
    const chart = (window.tvWidget || Object.values(window).find(v => v && v.chart && typeof v.chart === 'function'))?.chart?.();
    if (!chart) return 'no_chart';
    const levels = {lines_js};
    let drawn = 0;
    for (const lvl of levels) {{
        try {{
            const line = chart.createShape(
                {{ time: Math.floor(Date.now()/1000), price: lvl.price }},
                {{
                    shape: 'horizontal_line',
                    lock: false,
                    disableSelection: false,
                    text: lvl.label,
                    overrides: {{
                        linecolor: lvl.color,
                        linewidth: 1,
                        linestyle: 0,
                        showLabel: true,
                        textcolor: lvl.color,
                        fontsize: 11,
                        bold: false
                    }}
                }}
            );
            drawn++;
        }} catch(e) {{}}
    }}
    try {{ chart.chartModel().userEditedPriceScaleState && null; }} catch(e) {{}}
    return 'drew:' + drawn;
}})()
"""
    r = await eval_js(ws, js, cmd_id)
    return r.get('result', {}).get('result', {}).get('value', 'unknown')

async def save_chart(ws, cmd_id):
    js = """
(async () => {
    const widget = window.tvWidget || Object.values(window).find(v => v && v.chart && typeof v.chart === 'function');
    if (!widget) return 'no_widget';
    await new Promise(r => setTimeout(r, 500));
    try {
        if (widget.saveChartToServer) {
            widget.saveChartToServer(null, null, {});
            return 'saved';
        }
    } catch(e) {}
    return 'no_save';
})()
"""
    r = await eval_js(ws, js, cmd_id)
    return r.get('result', {}).get('result', {}).get('value', 'unknown')

def build_levels(t, side):
    levels = []
    def add(price, label, color):
        if price and price > 0:
            levels.append({"price": price, "label": f"{label}: ${price:.4f}" if price < 1 else f"{label}: ${price:.2f}", "color": color})

    # Red = Support levels
    add(t.get('sup_near'), 'S Near', '#ff4444')
    add(t.get('sup_strong'), 'S Strong', '#ff2222')
    add(t.get('sup_main'), 'S Main', '#cc0000')
    # Green = TP/targets
    add(t.get('short_target'), 'Short Tgt', '#00cc44')
    if side == 'LONG':
        add(t.get('entry_long_aggressive'), 'Entry Agg', '#44ff44')
        add(t.get('entry_long_conservative'), 'Entry Cons', '#22cc22')
    # Blue = Resistance, 52W, entry levels
    add(t.get('res_upper'), 'Res Upper', '#4488ff')
    add(t.get('res_near'), 'Res Near', '#6699ff')
    add(t.get('w52_high'), '52W High', '#88aaff')
    add(t.get('w52_low'), '52W Low', '#aabbff')
    add(t.get('short_opportunity'), 'Short Opp', '#ff8800')
    return levels

async def main():
    ws_url = get_chart_page()
    print(f"Connected to TradingView CDP")

    with open('_us_analysis_long.json') as f:
        long_data = json.load(f)
    with open('_us_analysis_short.json') as f:
        short_data = json.load(f)

    all_tickers = [(t, 'LONG') for t in long_data] + [(t, 'SHORT') for t in short_data]

    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        cmd_id = 1

        for i, (t, side) in enumerate(all_tickers):
            sym = t['symbol']
            print(f"  [{i+1}/{len(all_tickers)}] {sym} ({side})...", end=' ', flush=True)

            nav = await navigate_to(ws, sym, cmd_id); cmd_id += 1
            if 'no_widget' in str(nav):
                print(f"nav:{nav} SKIP")
                continue

            levels = build_levels(t, side)
            draw = await draw_levels(ws, sym, levels, cmd_id); cmd_id += 1
            save = await save_chart(ws, cmd_id); cmd_id += 1
            print(f"draw:{draw} save:{save}")

    print("\nDone drawing levels on all charts.")

asyncio.run(main())
