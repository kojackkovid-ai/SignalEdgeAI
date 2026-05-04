import urllib.request

url = 'https://signaledge-ai.fly.dev/health'
with urllib.request.urlopen(url, timeout=10) as resp:
    print(resp.status)
    print(resp.read().decode())
