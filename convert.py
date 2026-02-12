#!/usr/bin/env python3
"""
ИСПРАВЛЕННАЯ ВЕРСИЯ - фикс автопереключения и фильтрации
"""

import urllib.parse
import yaml

def parse_vless_url(vless_url):
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
    except:
        return None

def vless_to_clash_proxy(vless_params):
    proxy = {
        'name': vless_params['name'],
        'type': 'vless',
        'server': vless_params['server'],
        'port': vless_params['port'],
        'uuid': vless_params['uuid'],
        'network': vless_params.get('type', 'tcp'),
        'udp': True,
    }
    security = vless_params.get('security', '')
    if security == 'reality':
        proxy['tls'] = True
        proxy['servername'] = vless_params.get('sni', '')
        proxy['reality-opts'] = {
            'public-key': vless_params.get('pbk', ''),
            'short-id': vless_params.get('sid', ''),
        }
        flow = vless_params.get('flow', '')
        if flow:
            proxy['flow'] = flow
        fp = vless_params.get('fp', 'chrome')
        if fp:
            proxy['client-fingerprint'] = fp
    return proxy

def is_russia(name):
    """Проверяет российский ли сервер"""
    ru_keywords = ['🇷🇺', 'RUSSIA', 'RU', 'РФ', 'VK', 'YANDEX', 'SELECTEL', 
                   'BEGET', 'DELTA', '4VPS', 'AEZA', 'TIMEWEB']
    name_upper = name.upper()
    return any(kw in name_upper for kw in ru_keywords)

def is_germany(name):
    """Проверяет немецкий ли сервер"""
    de_keywords = ['🇩🇪', 'GERMANY', 'DE', 'DEUTSCHLAND', 'FRANKFURT', 
                   'BERLIN', 'MUNICH', 'HETZNER']
    name_upper = name.upper()
    return any(kw in name_upper for kw in de_keywords)

def is_poland(name):
    """Проверяет польский ли сервер"""
    pl_keywords = ['🇵🇱', 'POLAND', 'PL', 'POLSKA', 'WARSAW']
    name_upper = name.upper()
    return any(kw in name_upper for kw in pl_keywords)

def is_estonia(name):
    """Проверяет эстонский ли сервер"""
    ee_keywords = ['🇪🇪', 'ESTONIA', 'EE', 'EESTI', 'TALLINN']
    name_upper = name.upper()
    return any(kw in name_upper for kw in ee_keywords)

def is_hungary(name):
    """Проверяет венгерский ли сервер"""
    hu_keywords = ['🇭🇺', 'HUNGARY', 'HU', 'HUNGRY', 'MAGYAR', 'BUDAPEST']
    name_upper = name.upper()
    return any(kw in name_upper for kw in hu_keywords)

def convert_vless_to_clash():
    print("🔄 Читаю vless_lite.txt...")
    with open('vless_lite.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    vless_configs = []
    russian_configs = []
    non_russian_configs = []
    germany_configs = []
    poland_configs = []
    estonia_configs = []
    hungary_configs = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('vless://'):
            params = parse_vless_url(line)
            if params:
                vless_configs.append(params)
                name = params.get('name', '')
                
                if is_russia(name):
                    russian_configs.append(params)
                else:
                    non_russian_configs.append(params)
                
                if is_germany(name):
                    germany_configs.append(params)
                
                if is_poland(name):
                    poland_configs.append(params)
                
                if is_estonia(name):
                    estonia_configs.append(params)
                
                if is_hungary(name):
                    hungary_configs.append(params)
    
    print(f"📋 Всего конфигов: {len(vless_configs)}")
    print(f"🇷🇺 Российских: {len(russian_configs)}")
    print(f"🌍 Не-российских: {len(non_russian_configs)}")
    print(f"🇩🇪 Германия: {len(germany_configs)}")
    print(f"🇵🇱 Польша: {len(poland_configs)}")
    print(f"🇪🇪 Эстония: {len(estonia_configs)}")
    print(f"🇭🇺 Венгрия: {len(hungary_configs)}")
    
    if not vless_configs:
        print("❌ Не найдено валидных VLESS конфигураций!")
        return
    
    clash_proxies = []
    for params in vless_configs:
        proxy = vless_to_clash_proxy(params)
        clash_proxies.append(proxy)
    
    proxy_names = [p['name'] for p in clash_proxies]
    russian_names = [p['name'] for p in clash_proxies if is_russia(p['name'])]
    non_russian_names = [p['name'] for p in clash_proxies if not is_russia(p['name'])]
    germany_names = [p['name'] for p in clash_proxies if is_germany(p['name'])]
    poland_names = [p['name'] for p in clash_proxies if is_poland(p['name'])]
    estonia_names = [p['name'] for p in clash_proxies if is_estonia(p['name'])]
    hungary_names = [p['name'] for p in clash_proxies if is_hungary(p['name'])]
    
    # ФИКС: используем fallback вместо url-test для более стабильной работы
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
                'proxies': ['🚀 Авто', '📺 YouTube', '🎮 League', '🇩🇪 Frankfurt', '🇵🇱 Polska', '🇪🇪 Eesti', '🇭🇺 Hungary', '⚡ Российские'] + proxy_names[:30]
            },
            {
                'name': '🚀 Авто',
                'type': 'fallback',  # Изменено на fallback для надежности
                'proxies': proxy_names,
                'url': 'https://www.google.com/generate_204',
                'interval': 30,  # Проверка каждые 30 секунд
            },
            {
                'name': '📺 YouTube',
                'type': 'fallback',
                'proxies': non_russian_names if non_russian_names else proxy_names,
                'url': 'https://www.youtube.com/generate_204',
                'interval': 60,
            },
            {
                'name': '🎮 League',
                'type': 'fallback',  # fallback более надежен
                'proxies': russian_names if russian_names else proxy_names[:50],
                'url': 'https://www.google.com/generate_204',
                'interval': 30,
            },
            {
                'name': '🇩🇪 Frankfurt',
                'type': 'fallback',
                'proxies': germany_names if germany_names else non_russian_names[:30],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 30,
            },
            {
                'name': '🇵🇱 Polska',
                'type': 'fallback',
                'proxies': poland_names if poland_names else non_russian_names[:30],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 30,
            },
            {
                'name': '🇪🇪 Eesti',
                'type': 'fallback',
                'proxies': estonia_names if estonia_names else non_russian_names[:30],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 30,
            },
            {
                'name': '🇭🇺 Hungary',
                'type': 'fallback',
                'proxies': hungary_names if hungary_names else non_russian_names[:30],
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 30,
            },
            {
                'name': '⚡ Российские',
                'type': 'fallback',
                'proxies': russian_names if russian_names else proxy_names[:50],
                'url': 'https://yandex.ru/internet',
                'interval': 30,
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
            'DOMAIN-SUFFIX,hulu.com,📺 YouTube',
            'MATCH,PROXY'
        ]
    }
    
    with open('clash_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(clash_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Создано {len(clash_proxies)} прокси")
    print(f"🔧 ИСПРАВЛЕНИЯ:")
    print(f"   • Тип изменен на 'fallback' (надежнее)")
    print(f"   • Проверка каждые 30 секунд (чаще)")
    print(f"   • Улучшена фильтрация серверов")
    
    if len(germany_names) == 0:
        print(f"⚠️  ВНИМАНИЕ: Немецких серверов НЕ НАЙДЕНО!")
        print(f"   Frankfurt будет использовать любые НЕ-RU серверы")
    
    if len(russian_names) < 10:
        print(f"⚠️  ВНИМАНИЕ: Мало российских серверов ({len(russian_names)})")
    
    print("💾 Сохранено в clash_config.yaml")

if __name__ == "__main__":
    convert_vless_to_clash()
