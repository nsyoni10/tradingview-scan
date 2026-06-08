import json, asyncio, websockets, urllib.request

CDP_URL = "http://localhost:9222"

def get_chart_page():
    with urllib.request.urlopen(f"{CDP_URL}/json") as r:
        pages = json.loads(r.read())
    for p in pages:
        if 'tradingview' in p.get('url', ''):
            return p['webSocketDebuggerUrl']
    raise RuntimeError("TradingView chart page not found")

async def eval_js(ws, js, cmd_id=1):
    msg = json.dumps({"id": cmd_id, "method": "Runtime.evaluate", "params": {
        "expression": js, "awaitPromise": True, "timeout": 20000
    }})
    await ws.send(msg)
    while True:
        resp = json.loads(await ws.recv())
        if resp.get('id') == cmd_id:
            return resp.get('result', {}).get('result', {}).get('value', 'unknown')

async def main():
    long_syms = ['MJNA','UDR','NSC','MOD','BRX','MSM','AKR','DRH','SEM','NVGS']
    short_syms = ['ZBIO','TLK','BJ','ORI','KRMN','ESNT','TARS','ABT','B','SE']
    all_syms = long_syms + short_syms

    ws_url = get_chart_page()
    print(f"Adding {len(all_syms)} symbols to DAYSCAN...")

    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        syms_js = json.dumps(all_syms)
        js = f"""
(async () => {{
    const symbols = {syms_js};

    // Find watchlist model
    let model = null;
    for (const key of Object.keys(window)) {{
        try {{
            const obj = window[key];
            if (obj && obj.watchlistCollection && typeof obj.watchlistCollection === 'function') {{
                model = obj;
                break;
            }}
        }} catch(e) {{}}
    }}

    // Try via store
    if (!model) {{
        try {{
            const store = window.__STORE__ || window._store;
            if (store && store.getState) {{
                const state = store.getState();
                // look for watchlist in state
            }}
        }} catch(e) {{}}
    }}

    // Use clipboard/API method — navigate to each symbol and add via context
    // Best method: use the watchlist widget API
    const widget = window.tvWidget || Object.values(window).find(v => v && typeof v === 'object' && v.activeChart && typeof v.activeChart === 'function');

    // Try internal watchlist manager
    const managers = Object.values(window).filter(v => {{
        try {{ return v && typeof v.addSymbol === 'function' && typeof v.getSymbols === 'function'; }} catch(e) {{ return false; }}
    }});

    if (managers.length > 0) {{
        const mgr = managers[0];
        let added = 0;
        for (const sym of symbols) {{
            try {{ mgr.addSymbol(sym); added++; }} catch(e) {{}}
        }}
        return 'added_via_manager:' + added;
    }}

    return 'no_manager_found';
}})()
"""
        result = await eval_js(ws, js, 1)
        print(f"Direct API result: {result}")

        if 'no_manager' in str(result):
            # Use tv_watchlist_pivot.py approach instead
            print("Using watchlist script...")
            return 'use_script'

    return result

result = asyncio.run(main())
print(f"Result: {result}")
