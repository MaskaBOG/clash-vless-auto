#!/usr/bin/env python3
"""
Конвертер Durev VPN → Clash YAML
Скачивает подписку от Durev и конвертирует в Clash формат
"""

import urllib.parse
import yaml
import base64
import requests

# ТВОЯ ССЫЛКА НА DUREV ПОДПИСКУ
DUREV_SUBSCRIPTION_URL = "https://your-durev.com/sub/utEkqudsrUGR6KulBfFNw3/about/"

def parse_vless_url(vless_url):
    """Парсит VLESS URL в параметры"""
    try:
        url_data = vless_url.replace('vless://', '')
        if '@' not in url_data:
            return None
        
        uuid_part, rest = url_data.split('@', 1)
        
        if '?' not in rest:
            return None
        
        server_part, params_and_name = rest.split('?', 1)
        
        if ':' in server_part:
            server, port = server_part.split(':', 1)
        else:
            return None
        
        if '#' in params_and_name:
            params_str, name = params_and_name.split('#', 1)
            name = urllib.parse.unquote(name)
        else:
            params_str = params_and_name
            name = server
        
        params = urllib.parse.parse_qs(params_str)
        
        result = {
            'uuid': uuid_part,
            'server': server,
            'port': int(port),
            'name': name,
        }
        
        for key, values in params.items():
            if values:
                result[key] = values[0]
        
        return result
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return None

def vless_to_clash_proxy(params):
    """Конвертирует VLESS параметры в Clash прокси"""
    try:
        security = params.get('security', '')
        
        proxy = {
            'name': params['name'],
            'type': 'vless',
            'server': params['server'],
            'port': params['port'],
            'uuid': params['uuid'],
            'network': params.get('type', 'tcp'),
            'udp': True,
        }
        
        if security == 'reality':
            proxy['tls'] = True
            proxy['servername'] = params.get('sni', '')
            
            sid = str(params.get('sid', '')).strip()
            
            proxy['reality-opts'] = {
                'public-key': params.get('pbk', ''),
                'short-id': sid,
            }
            
            flow = params.get('flow', '')
            if flow:
                proxy['flow'] = flow
            
            fp = params.get('fp', 'chrome')
            if fp:
                proxy['client-fingerprint'] = fp
            
            # XHTTP настройки
            mode = params.get('mode', '')
            if mode:
                proxy['xhttp-opts'] = {
                    'mode': mode,
                }
                
                path = params.get('path', '')
                if path:
                    proxy['xhttp-opts']['path'] = path
                    
                concurrency = params.get('concurrency', '')
                if concurrency:
                    proxy['xhttp-opts']['concurrency'] = int(concurrency)
        
        return proxy
        
    except Exception as e:
        print(f"❌ Convert error for {params.get('name', 'unknown')}: {e}")
        return None

def download_durev_subscription():
    """Скачивает подписку Durev"""
    print(f"📥 Скачиваю подписку Durev...")
    try:
        response = requests.get(DUREV_SUBSCRIPTION_URL, timeout=30)
        response.raise_for_status()
        
        # Декодируем Base64
        base64_data = response.text.strip()
        decoded_data = base64.b64decode(base64_data).decode('utf-8')
        
        # Разбиваем на строки
        vless_urls = decoded_data.strip().split('\n')
        
        print(f"✅ Получено {len(vless_urls)} серверов")
        return vless_urls
        
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return []

def convert_durev_to_clash():
    """Главная функция конвертации"""
    print("🔄 Конвертация Durev VPN → Clash YAML")
    print("=" * 60)
    
    # Скачиваем подписку
    vless_urls = download_durev_subscription()
    
    if not vless_urls:
        print("❌ Не удалось скачать подписку!")
        return
    
    # Парсим VLESS URLs
    print("🔍 Парсинг конфигов...")
    vless_configs = []
    for url in vless_urls:
        url = url.strip()
        if url.startswith('vless://'):
            params = parse_vless_url(url)
            if params:
                vless_configs.append(params)
    
    print(f"✅ Распарсено: {len(vless_configs)} конфигов")
    
    # Конвертируем в Clash
    print("⚙️  Конвертация в Clash формат...")
    clash_proxies = []
    skipped = 0
    
    for params in vless_configs:
        proxy = vless_to_clash_proxy(params)
        if proxy:
            clash_proxies.append(proxy)
        else:
            skipped += 1
    
    print(f"✅ Сконвертировано: {len(clash_proxies)} прокси")
    print(f"⚠️  Пропущено: {skipped}")
    
    if not clash_proxies:
        print("❌ Нет валидных прокси!")
        return
    
    # Создаём группы
    proxy_names = [p['name'] for p in clash_proxies]
    
    # Классифицируем по странам
    russia_names = [n for n in proxy_names if '🇷🇺' in n or 'Russia' in n]
    germany_names = [n for n in proxy_names if '🇩🇪' in n or 'Germany' in n]
    poland_names = [n for n in proxy_names if '🇵🇱' in n or 'Poland' in n]
    netherlands_names = [n for n in proxy_names if '🇳🇱' in n or 'Netherlands' in n]
    
    print(f"🇷🇺 Российских: {len(russia_names)}")
    print(f"🇩🇪 Немецких: {len(germany_names)}")
    print(f"🇵🇱 Польских: {len(poland_names)}")
    print(f"🇳🇱 Голландских: {len(netherlands_names)}")
    
    # Создаём Clash конфиг
    clash_config = {
        'mixed-port': 7890,
        'allow-lan': True,
        'mode': 'rule',
        'log-level': 'info',
        'external-controller': '127.0.0.1:9090',
        'dns': {
            'enable': True,
            'enhanced-mode': 'fake-ip',
            'fake-ip-range': '198.18.0.1/16',
            'nameserver': ['8.8.8.8', '1.1.1.1'],
        },
        'proxies': clash_proxies,
        'proxy-groups': [
            {
                'name': 'PROXY',
                'type': 'select',
                'proxies': ['🚀 Авто', '📺 YouTube', '🎮 League', '🇩🇪 Германия', '🇵🇱 Польша', '🇳🇱 Нидерланды', '⚡ Россия'] + proxy_names[:20]
            },
            {
                'name': '🚀 Авто',
                'type': 'url-test',
                'proxies': proxy_names,
                'url': 'https://www.google.com/generate_204',
                'interval': 60,
                'tolerance': 100,
            },
            {
                'name': '📺 YouTube',
                'type': 'url-test',
                'proxies': [n for n in proxy_names if '🇷🇺' not in n and 'Russia' not in n],
                'url': 'https://www.youtube.com/generate_204',
                'interval': 120,
                'tolerance': 150,
            },
            {
                'name': '🎮 League',
                'type': 'url-test',
                'proxies': russia_names if russia_names else proxy_names[:20],
                'url': 'https://www.google.com/generate_204',
                'interval': 60,
                'tolerance': 30,
            },
            {
                'name': '🇩🇪 Германия',
                'type': 'url-test',
                'proxies': germany_names if germany_names else proxy_names[:10],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '🇵🇱 Польша',
                'type': 'url-test',
                'proxies': poland_names if poland_names else proxy_names[:10],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '🇳🇱 Нидерланды',
                'type': 'url-test',
                'proxies': netherlands_names if netherlands_names else proxy_names[:10],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '⚡ Россия',
                'type': 'url-test',
                'proxies': russia_names if russia_names else proxy_names[:10],
                'url': 'https://yandex.ru/internet',
                'interval': 60,
                'tolerance': 30,
            }
        ],
        'rules': [
            'DOMAIN-SUFFIX,youtube.com,📺 YouTube',
            'DOMAIN-SUFFIX,googlevideo.com,📺 YouTube',
            'DOMAIN-SUFFIX,ytimg.com,📺 YouTube',
            'DOMAIN-SUFFIX,ggpht.com,📺 YouTube',
            'DOMAIN-SUFFIX,youtu.be,📺 YouTube',
            'DOMAIN,youtube.googleapis.com,📺 YouTube',
            'DOMAIN-SUFFIX,twitch.tv,📺 YouTube',
            'DOMAIN-SUFFIX,netflix.com,📺 YouTube',
            'MATCH,PROXY'
        ]
    }
    
    # Сохраняем
    with open('clash_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(clash_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False, default_style="'")
    
    print("=" * 60)
    print(f"💾 Сохранено: clash_config.yaml")
    print(f"📊 Всего серверов: {len(clash_proxies)}")
    print(f"✅ ГОТОВО для Clash Verge!")

if __name__ == "__main__":
    convert_durev_to_clash()
