#!/usr/bin/env python3
"""
Автоматический конвертер VLESS → Clash YAML
С валидацией short-id и исключением RU из EU групп
"""

import urllib.parse
import yaml
import re

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

def is_valid_short_id(sid):
    """Строгая проверка short-id для REALITY"""
    if not sid:
        return True  # Пустой валиден
    
    sid = sid.strip()
    
    # ТОЛЬКО hex символы (0-9, a-f, A-F)
    if not re.match(r'^[0-9a-fA-F]+$', sid):
        return False
    
    # Максимум 16 символов
    if len(sid) > 16:
        return False
    
    return True

def vless_to_clash_proxy(vless_params):
    """Конвертирует VLESS в Clash, возвращает None если невалидный"""
    try:
        security = vless_params.get('security', '')
        
        # КРИТИЧЕСКАЯ ВАЛИДАЦИЯ ДЛЯ REALITY
        if security == 'reality':
            sid = vless_params.get('sid', '')
            
            # Если short-id битый - ПРОПУСКАЕМ весь сервер!
            if not is_valid_short_id(sid):
                print(f"⚠️  SKIP: {vless_params['name'][:60]} | invalid sid: '{sid}'")
                return None
        
        proxy = {
            'name': vless_params['name'],
            'type': 'vless',
            'server': vless_params['server'],
            'port': vless_params['port'],
            'uuid': vless_params['uuid'],
            'network': vless_params.get('type', 'tcp'),
            'udp': True,
        }
        
        if security == 'reality':
            proxy['tls'] = True
            proxy['servername'] = vless_params.get('sni', '')
            
            sid = vless_params.get('sid', '').strip()
            
            proxy['reality-opts'] = {
                'public-key': vless_params.get('pbk', ''),
                'short-id': sid,
            }
            
            flow = vless_params.get('flow', '')
            if flow:
                proxy['flow'] = flow
            
            fp = vless_params.get('fp', 'chrome')
            if fp:
                proxy['client-fingerprint'] = fp
        
        return proxy
        
    except Exception as e:
        print(f"❌ Error: {vless_params.get('name', 'unknown')}: {e}")
        return None

def is_russia(name):
    """Проверяет российский ли сервер"""
    ru_keywords = [
        '🇷🇺', 'RUSSIA', 'RU', 'РФ', 
        'VK', 'YANDEX', 'SELECTEL', 'BEGET', 'DELTA', 
        '4VPS', 'AEZA', 'TIMEWEB', 'MOSCOW', 'PETERSBURG',
        'SPB', 'MSK', 'ROSTELECOM', 'MEGAFON', 'MTS'
    ]
    name_upper = name.upper()
    return any(kw in name_upper for kw in ru_keywords)

def is_germany(name):
    """Проверяет немецкий ли сервер (БЕЗ российских!)"""
    de_keywords = ['🇩🇪', 'GERMANY', 'DEUTSCHLAND', 'FRANKFURT', 
                   'BERLIN', 'MUNICH', 'HETZNER', 'NUREMBERG']
    name_upper = name.upper()
    return any(kw in name_upper for kw in de_keywords) and not is_russia(name)

def is_poland(name):
    """Проверяет польский ли сервер (БЕЗ российских!)"""
    pl_keywords = ['🇵🇱', 'POLAND', 'POLSKA', 'WARSAW', 'KRAKOW']
    name_upper = name.upper()
    return any(kw in name_upper for kw in pl_keywords) and not is_russia(name)

def is_estonia(name):
    """Проверяет эстонский ли сервер (БЕЗ российских!)"""
    ee_keywords = ['🇪🇪', 'ESTONIA', 'EESTI', 'TALLINN']
    name_upper = name.upper()
    return any(kw in name_upper for kw in ee_keywords) and not is_russia(name)

def is_hungary(name):
    """Проверяет венгерский ли сервер (БЕЗ российских!)"""
    hu_keywords = ['🇭🇺', 'HUNGARY', 'MAGYAR', 'BUDAPEST']
    name_upper = name.upper()
    return any(kw in name_upper for kw in hu_keywords) and not is_russia(name)

def convert_vless_to_clash():
    print("🔄 Читаю vless_lite.txt...")
    with open('vless_lite.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    vless_configs = []
    for line in lines:
        line = line.strip()
        if line.startswith('vless://'):
            params = parse_vless_url(line)
            if params:
                vless_configs.append(params)
    
    print(f"📋 Всего конфигов: {len(vless_configs)}")
    
    if not vless_configs:
        print("❌ Не найдено валидных VLESS конфигураций!")
        return
    
    # Конвертация с ВАЛИДАЦИЕЙ
    print("🔍 Валидация и конвертация...")
    clash_proxies = []
    skipped = 0
    
    for params in vless_configs:
        proxy = vless_to_clash_proxy(params)
        if proxy:
            clash_proxies.append(proxy)
        else:
            skipped += 1
    
    print(f"✅ Валидных прокси: {len(clash_proxies)}")
    print(f"⚠️  Пропущено битых: {skipped}")
    
    if len(clash_proxies) == 0:
        print("❌ НЕТ валидных прокси!")
        return
    
    # Классификация
    russian_configs = []
    non_russian_configs = []
    germany_configs = []
    poland_configs = []
    estonia_configs = []
    hungary_configs = []
    
    for proxy in clash_proxies:
        name = proxy['name']
        
        if is_russia(name):
            russian_configs.append(proxy)
        else:
            non_russian_configs.append(proxy)
        
        if is_germany(name):
            germany_configs.append(proxy)
        
        if is_poland(name):
            poland_configs.append(proxy)
        
        if is_estonia(name):
            estonia_configs.append(proxy)
        
        if is_hungary(name):
            hungary_configs.append(proxy)
    
    print(f"🇷🇺 Российских: {len(russian_configs)}")
    print(f"🌍 Не-российских: {len(non_russian_configs)}")
    print(f"🇩🇪 Германия: {len(germany_configs)}")
    print(f"🇵🇱 Польша: {len(poland_configs)}")
    print(f"🇪🇪 Эстония: {len(estonia_configs)}")
    print(f"🇭🇺 Венгрия: {len(hungary_configs)}")
    
    proxy_names = [p['name'] for p in clash_proxies]
    russian_names = [p['name'] for p in clash_proxies if is_russia(p['name'])]
    non_russian_names = [p['name'] for p in clash_proxies if not is_russia(p['name'])]
    germany_names = [p['name'] for p in clash_proxies if is_germany(p['name'])]
    poland_names = [p['name'] for p in clash_proxies if is_poland(p['name'])]
    estonia_names = [p['name'] for p in clash_proxies if is_estonia(p['name'])]
    hungary_names = [p['name'] for p in clash_proxies if is_hungary(p['name'])]
    
    # Фолбэки если стран нет
    if not germany_names:
        germany_names = non_russian_names[:30] if non_russian_names else proxy_names[:30]
    if not poland_names:
        poland_names = non_russian_names[:30] if non_russian_names else proxy_names[:30]
    if not estonia_names:
        estonia_names = non_russian_names[:30] if non_russian_names else proxy_names[:30]
    if not hungary_names:
        hungary_names = non_russian_names[:30] if non_russian_names else proxy_names[:30]
    
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
                'type': 'url-test',
                'proxies': proxy_names,
                'url': 'https://www.google.com/generate_204',
                'interval': 60,
                'tolerance': 100,
            },
            {
                'name': '📺 YouTube',
                'type': 'url-test',
                'proxies': non_russian_names if non_russian_names else proxy_names,
                'url': 'https://www.youtube.com/generate_204',
                'interval': 120,
                'tolerance': 150,
            },
            {
                'name': '🎮 League',
                'type': 'url-test',
                'proxies': russian_names if russian_names else proxy_names[:50],
                'url': 'https://www.google.com/generate_204',
                'interval': 60,
                'tolerance': 30,
            },
            {
                'name': '🇩🇪 Frankfurt',
                'type': 'url-test',
                'proxies': germany_names,
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '🇵🇱 Polska',
                'type': 'url-test',
                'proxies': poland_names,
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '🇪🇪 Eesti',
                'type': 'url-test',
                'proxies': estonia_names,
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '🇭🇺 Hungary',
                'type': 'url-test',
                'proxies': hungary_names,
                'url': 'https://cloudflare.com/cdn-cgi/trace',
                'interval': 60,
                'tolerance': 50,
            },
            {
                'name': '⚡ Российские',
                'type': 'url-test',
                'proxies': russian_names if russian_names else proxy_names[:50],
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
            'DOMAIN-SUFFIX,hulu.com,📺 YouTube',
            'MATCH,PROXY'
        ]
    }
    
    with open('clash_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(clash_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"💾 Сохранено: clash_config.yaml")
    print(f"✅ ГОТОВО!")

if __name__ == "__main__":
    convert_vless_to_clash()
