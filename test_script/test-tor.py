import requests

proxies = {'http': 'socks5h://127.0.0.1:9050'}
ip = requests.get('http://httpbin.org/ip', proxies=proxies).text
print(ip)  # Should show a Tor exit node IP
