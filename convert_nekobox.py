"""
Конвертер VLESS → Base64 список для NekoBox
Генерирует файл nekobox_subscription.txt
"""

import urllib.parse
import base64
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
    """Валидация short-id"""
    sid = str(sid) if sid is not None else ''
    sid = sid.strip()
    
    if not sid:
        return False
    
    if not re.match(r'^[0-9a-fA-F]+$', sid):
        return False
    
    if len(sid) > 16:
        return False
    
    return True

def vless_params_to_url(params):
    """Конвертирует параметры обратно в VLESS URL"""
    try:
        security = params.get('security', '')
        
        # Валидация для REALITY
        if security == 'reality':
            sid = params.get('sid', '')
            if not is_valid_short_id(sid):
                print(f"⚠️  SKIP: {params['name'][:60]} | invalid sid")
                return None
        
        # Строим URL
        url = f"vless://{params['uuid']}@{params['server']}:{params['port']}"
        
        # Параметры
        query_params = []
        
        if params.get('type'):
            query_params.append(f"type={params['type']}")
        
        if security:
            query_params.append(f"security={security}")
        
        if security == 'reality':
            if params.get('sni'):
                query_params.append(f"sni={params['sni']}")
            if params.get('pbk'):
                query_params.append(f"pbk={params['pbk']}")
            sid = str(params.get('sid', '')).strip()
            if sid:  # Только если не пустой
                query_params.append(f"sid={sid}")
            if params.get('fp'):
                query_params.append(f"fp={params['fp']}")
            if params.get('flow'):
                query_params.append(f"flow={params['flow']}")
        
        # Добавляем параметры к URL
        if query_params:
            url += "?" + "&".join(query_params)
        
        # Добавляем имя
        name_encoded = urllib.parse.quote(params['name'])
        url += f"#{name_encoded}"
        
        return url
        
    except Exception as e:
        print(f"❌ Error: {params.get('name', 'unknown')}: {e}")
        return None

def convert_vless_to_nekobox():
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
    
    # Конвертируем обратно в VLESS URLs с валидацией
    print("🔍 Валидация и конвертация...")
    valid_urls = []
    skipped = 0
    
    for params in vless_configs:
        url = vless_params_to_url(params)
        if url:
            valid_urls.append(url)
        else:
            skipped += 1
    
    print(f"✅ Валидных: {len(valid_urls)}")
    print(f"⚠️  Пропущено: {skipped}")
    
    if len(valid_urls) == 0:
        print("❌ НЕТ валидных прокси!")
        return
    
    # Создаём Base64 список
    urls_text = "\n".join(valid_urls)
    base64_encoded = base64.b64encode(urls_text.encode('utf-8')).decode('utf-8')
    
    # Сохраняем
    with open('nekobox_subscription.txt', 'w', encoding='utf-8') as f:
        f.write(base64_encoded)
    
    print(f"💾 Сохранено: nekobox_subscription.txt")
    print(f"📊 Серверов в подписке: {len(valid_urls)}")
    print(f"✅ ГОТОВО для NekoBox!")

if __name__ == "__main__":
    convert_vless_to_nekobox()
