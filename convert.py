#!/usr/bin/env python3
"""
ФИКС ВАЛИДАЦИИ - проверка и исправление битых short-id
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

def validate_short_id(sid):
    """Валидирует short-id для REALITY"""
    if not sid:
        return ""  # Пустой short-id валиден
    
    # Удаляем пробелы
    sid = sid.strip()
    
    # Проверяем что это hex-строка (только 0-9, a-f, A-F)
    if not re.match(r'^[0-9a-fA-F]*$', sid):
        print(f"⚠️  Невалидный short-id: {sid} (содержит не-hex символы) → очистка")
        return ""
    
    # Проверяем длину (максимум 16 символов)
    if len(sid) > 16:
        print(f"⚠️  Слишком длинный short-id: {sid} (длина {len(sid)}) → обрезка")
        return sid[:16]
    
    return sid

def vless_to_clash_proxy(vless_params):
    try:
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
            # ВАЛИДАЦИЯ SHORT-ID!
            raw_sid = vless_params.get('sid', '')
            validated_sid = validate_short_id(raw_sid)
            
            proxy['tls'] = True
            proxy['servername'] = vless_params.get('sni', '')
            proxy['reality-opts'] = {
                'public-key': vless_params.get('pbk', ''),
                'short-id': validated_sid,  # Используем валидированный!
            }
            
            flow = vless_params.get('flow', '')
            if flow:
                proxy['flow'] = flow
            
            fp = vless_params.get('fp', 'chrome')
            if fp:
                proxy['client-fingerprint'] = fp
        
        return proxy
    except Exception as e:
        print(f"❌ Ошибка конвертации прокси {vless_params.get('name', 'unknown')}: {e}")
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
    de_keywords = ['🇩🇪', 'GERMANY', 'DEUTSCHLAND', 'FRANKFURT', 
                   'BERLIN', 'MUNICH', 'HETZNER', 'NUREMBERG']
    name_upper = name.upper()
    return any(kw in name_upper for kw in de_keywords) and not is_russia(name)

def is_poland(name):
    pl_keywords = ['🇵🇱', 'POLAND', 'POLSKA', 'WARSAW', 'KRAKOW']
    name_upper = name.upper()
    return any(kw in name_upper for kw in pl_keywords) and not is_russia(name)

def is_estonia(name):
    ee_keywords = ['🇪🇪', 'ESTONIA', 'EESTI', 'TALLINN']
    name_upper = name.upper()
    return any(kw in name_upper for kw in ee_keywords) and not is_russia(name)

def is_hungary(name):
    hu_keywords = ['🇭🇺', 'HUNGARY', 'MAGYAR', 'BUDAPEST']
    name_upper = name.upper()
    return any(kw in name_upper for kw in hu_keywords) and not is_russia(name)

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
    
    skipped = 0
    
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
    
    # Конвертируем с валидацией
    clash_proxies = []
    for params in vless_configs:
        proxy = vless_to_clash_proxy(params)
        if proxy:  # Только валидные прокси
            clash_proxies.append(proxy)
        else:
            skipped += 1
    
    if skipped > 0:
        print(f"⚠️  Пропущено {skipped} невалидных прокси")
    
    proxy_names = [p['name'] for p in clash_proxies]
    russian_names = [p['name'] for p in clash_proxies if is_russia(p['name'])]
    non_russian_names = [p['name'] for p in clash_proxies if not is_russia(p['name'])]
    
    germany_names = [p['name'] for p in clash_proxies if is_germany(p['name'])]
    poland_names = [p['name'] for p in clash_proxies if is_poland(p['name'])]
    estonia_names = [p['name'] for p in clash_proxies if is_estonia(p['name'])]
    hungary_names = [p['name'] for p in clash_proxies if is_hungary(p['name'])]
    
    # Фолбэки если конкретных стран нет
    if not germany_names:
        germany_names = non_russian_names[:30]
    if not poland_names:
        poland_names = non_russian_names[:30]
    if not estonia_names:
        estonia_names = non_russian_names[:30]
    if not hungary_names:
        hungary_names = non_russian_names[:30]
    
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
    
    print(f"✅ Создано {len(clash_proxies)} валидных прокси")
    print(f"🔧 ВАЛИДАЦИЯ:")
    print(f"   ✅ short-id проверяются и исправляются")
    print(f"   ✅ Битые прокси пропускаются")
    print(f"   ✅ Российские исключены из EU групп")
    print("💾 Сохранено в clash_config.yaml")

if __name__ == "__main__":
    convert_vless_to_clash()
