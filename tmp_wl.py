import urllib.request, json, websocket, time

pages = json.loads(urllib.request.urlopen("http://localhost:9222/json", timeout=5).read())
page = next((p for p in pages if "tradingview.com/chart" in p.get("url","")), None)
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20, header={"Origin": "http://localhost"})

def js(code, mid=1):
    ws.send(json.dumps({"id":mid,"method":"Runtime.evaluate","params":{"expression":code,"returnByValue":True}}))
    ws.settimeout(15)
    for _ in range(200):
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            return r.get("result",{}).get("result",{}).get("value","")

# open watchlist panel first
js("""(function(){
  var btn = document.querySelector('[data-name="base"]');
  if(btn && btn.getAttribute("aria-pressed") !== "true") btn.click();
})()""")
time.sleep(1.5)

# dump ALL data-name values now
r = js("""(function(){
  var names = [];
  document.querySelectorAll("[data-name]").forEach(function(el){
    names.push(el.getAttribute("data-name") + "|" + el.tagName + "|" + el.offsetWidth + "x" + el.offsetHeight);
  });
  return JSON.stringify([...new Set(names)]);
})()""", 2)
print(r)
ws.close()
