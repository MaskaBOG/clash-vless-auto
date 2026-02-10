#!/usr/bin/env python3
"""
Автоматический конвертер VLESS → Clash YAML
С отдельными группами для Польши, Эстонии, Венгрии и Германии
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

def is_country(name, country_codes):
    """Проверяет содержит ли имя коды стран"""
    name_upper = name.upper()
    for code in country_codes:
        if code.upper() in name_upper:
            return True
    return False

def convert_vless_to_clash():
    print("🔄 Читаю vless_lite.txt...")
    with open('vless_lite.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    vless_configs = []
    russian_configs = []
    non_russian_configs = []
    poland_configs = []
    estonia_configs = []
    hungary_configs = []
    germany_configs = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('vless://'):
            params = parse_vless_url(line)
            if params:
                vless_configs.append(params)
                name = params.get('name', '')
                
                # Российские серверы
                if is_country(name, ['🇷🇺', 'Russia', 'RU', 'РФ']):
                    russian_configs.append(params)
                else:
                    non_russian_configs.append(params)
                
                # Польша
                if is_country(name, ['🇵🇱', 'Poland', 'PL', 'Polska']):
                    poland_configs.append(params)
                
                # Эстония
                if is_country(name, ['🇪🇪', 'Estonia', 'EE', 'Eesti']):
                    estonia_configs.append(params)
                
                # Венгрия
                if is_country(name, ['🇭🇺', 'Hungary', 'HU', 'Hungry', 'Magyarország']):
                    hungary_configs.append(params)
                
                # Германия
                if is_country(name, ['🇩🇪', 'Germany', 'DE', 'Deutschland', 'Frankfurt', 'Berlin', 'Munich']):
                    germany_configs.append(params)
    
    print(f"📋 Всего конфигов: {len(vless_configs)}")
    print(f"🇷🇺 Российских: {len(russian_configs)}")
    print(f"🌍 Не-российских: {len(non_russian_configs)}")
    print(f"🇵🇱 Польша: {len(poland_configs)}")
    print(f"🇪🇪 Эстония: {len(estonia_configs)}")
    print(f"🇭🇺 Венгрия: {len(hungary_configs)}")
    print(f"🇩🇪 Германия: {len(germany_configs)}")
    
    if not vless_configs:
        print("❌ Не найдено валидных VLESS конфигураций!")
        return
    
    # Конвертируем в Clash формат
    clash_proxies = []
    for params in vless_configs:
        proxy = vless_to_clash_proxy(params)
        clash_proxies.append(proxy)
    
    proxy_names = [p['name'] for p in clash_proxies]
    russian_names = [p['name'] for p in clash_proxies 
                     if is_country(p['name'], ['🇷🇺', 'Russia', 'RU'])]
    non_russian_names = [p['name'] for p in clash_proxies 
                         if not is_country(p['name'], ['🇷🇺', 'Russia', 'RU'])]
    poland_names = [p['name'] for p in clash_proxies 
                    if is_country(p['name'], ['🇵🇱', 'Poland', 'PL'])]
    estonia_names = [p['name'] for p in clash_proxies 
                     if is_country(p['name'], ['🇪🇪', 'Estonia', 'EE'])]
    hungary_names = [p['name'] for p in clash_proxies 
                     if is_country(p['name'], ['🇭🇺', 'Hungary', 'HU'])]
    germany_names = [p['name'] for p in clash_proxies 
                     if is_country(p['name'], ['🇩🇪', 'Germany', 'DE', 'Frankfurt'])]
    
    # Умная конфигурация с отдельными группами для каждой страны
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
                'proxies': ['🚀 Авто', '📺 YouTube', '🎮 League', '🇩🇪 Frankfurt', '🇵🇱 Polska', '🇪🇪 Eesti', '🇭🇺 Hungary', '⚡ Российские', '🌍 Зарубежные'] + proxy_names[:30]
            },
            {
                'name': '🚀 Авто',
                'type': 'url-test',
                'proxies': proxy_names,
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 60,
                'tolerance': 100,
                'lazy': False
            },
            {
                'name': '📺 YouTube',
                'type': 'url-test',
                'proxies': non_russian_names if non_russian_names else proxy_names,
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 120,
                'tolerance': 150
            },
            {
                'name': '🎮 League',
                'type': 'url-test',
                'proxies': russian_names[:50] if russian_names else proxy_names[:50],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 120,
                'tolerance': 30
            },
            {
                'name': '🇩🇪 Frankfurt',
                'type': 'url-test',
                'proxies': germany_names if germany_names else non_russian_names[:20],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 120,
                'tolerance': 30
            },
            {
                'name': '🇵🇱 Polska',
                'type': 'url-test',
                'proxies': poland_names if poland_names else non_russian_names[:20],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 120,
                'tolerance': 30
            },
            {
                'name': '🇪🇪 Eesti',
                'type': 'url-test',
                'proxies': estonia_names if estonia_names else non_russian_names[:20],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 120,
                'tolerance': 30
            },
            {
                'name': '🇭🇺 Hungary',
                'type': 'url-test',
                'proxies': hungary_names if hungary_names else non_russian_names[:20],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 120,
                'tolerance': 30
            },
            {
                'name': '⚡ Российские',
                'type': 'url-test',
                'proxies': russian_names if russian_names else proxy_names[:100],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 60,
                'tolerance': 50
            },
            {
                'name': '🌍 Зарубежные',
                'type': 'url-test',
                'proxies': non_russian_names if non_russian_names else proxy_names[:100],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 60,
                'tolerance': 100
            }
        ],
        'rules': [
            # YouTube и Google сервисы - только через не-российские серверы
            'DOMAIN-SUFFIX,youtube.com,📺 YouTube',
            'DOMAIN-SUFFIX,googlevideo.com,📺 YouTube',
            'DOMAIN-SUFFIX,ytimg.com,📺 YouTube',
            'DOMAIN-SUFFIX,ggpht.com,📺 YouTube',
            'DOMAIN-SUFFIX,youtu.be,📺 YouTube',
            'DOMAIN,youtube.googleapis.com,📺 YouTube',
            
            # Другие видео-сервисы
            'DOMAIN-SUFFIX,twitch.tv,📺 YouTube',
            'DOMAIN-SUFFIX,netflix.com,📺 YouTube',
            'DOMAIN-SUFFIX,hulu.com,📺 YouTube',
            
            # Всё остальное - через умный выбор
            'MATCH,PROXY'
        ]
    }
    
    with open('clash_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(clash_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Создано {len(clash_proxies)} прокси")
    print(f"🎯 Отдельные группы по странам:")
    print(f"   🇩🇪 Frankfurt (Germany) - {len(germany_names)} серверов")
    print(f"   🇵🇱 Polska - {len(poland_names)} серверов")
    print(f"   🇪🇪 Eesti - {len(estonia_names)} серверов")
    print(f"   🇭🇺 Hungary - {len(hungary_names)} серверов")
    print(f"   🎮 League - RU серверы ({len(russian_names[:50])} шт)")
    print(f"   📺 YouTube - Не-RU серверы")
    print("💾 Сохранено в clash_config.yaml")

if __name__ == "__main__":
    convert_vless_to_clash()
