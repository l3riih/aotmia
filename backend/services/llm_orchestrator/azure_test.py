#!/usr/bin/env python3
import socket
import requests
import json
from src.config import config

print("=" * 60)
print("🔧 DIAGNÓSTICO DE CONECTIVIDAD AZURE AI") 
print("=" * 60)

# Test DNS
hostname = config.azure_ai_endpoint.replace('https://', '').replace('/models', '')
print(f"🔍 Probando DNS: {hostname}")

try:
    ip = socket.gethostbyname(hostname)
    print(f"✅ DNS resuelto: {hostname} -> {ip}")
    dns_ok = True
except socket.gaierror as e:
    print(f"❌ Error DNS: {e}")
    dns_ok = False

if dns_ok:
    # Test HTTP básico
    base_url = config.azure_ai_endpoint.replace('/models', '')
    print(f"🌐 Probando HTTP: {base_url}")
    
    try:
        response = requests.get(base_url, timeout=15, headers={
            'Authorization': f'Bearer {config.azure_ai_key}',
            'User-Agent': 'Atomia-Test/1.0'
        })
        print(f"✅ HTTP Status: {response.status_code}")
        
        # Test chat completions
        if response.status_code < 500:
            url = f"{config.azure_ai_endpoint}/chat/completions"
            print(f"🤖 Probando: {url}")
            
            payload = {
                "model": config.azure_ai_model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {config.azure_ai_key}'
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                print(f"📡 Chat Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ ¡Conectividad exitosa!")
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(f"Respuesta: {response.text[:300]}")
            except Exception as e:
                print(f"❌ Error en chat: {e}")
                
    except Exception as e:
        print(f"❌ Error HTTP: {e}")

print("=" * 60)
