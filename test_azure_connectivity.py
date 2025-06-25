#!/usr/bin/env python3
"""
Script de diagnóstico para conectividad con Azure AI
"""
import requests
import json
import os
from src.config import config

def test_dns_resolution():
    """Test de resolución DNS del endpoint"""
    import socket
    hostname = config.azure_ai_endpoint.replace('https://', '').replace('/models', '')
    print(f"🔍 Probando resolución DNS para: {hostname}")
    
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS resuelto: {hostname} -> {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ Error DNS: {e}")
        return False

def test_basic_connectivity():
    """Test de conectividad HTTP básica"""
    base_url = config.azure_ai_endpoint.replace('/models', '')
    print(f"🌐 Probando conectividad HTTP a: {base_url}")
    
    try:
        response = requests.get(base_url, timeout=15, headers={
            'Authorization': f'Bearer {config.azure_ai_key}',
            'User-Agent': 'Atomia-Diagnostic/1.0'
        })
        print(f"✅ HTTP Status: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chat_completions_endpoint():
    """Test del endpoint específico de chat completions"""
    url = f"{config.azure_ai_endpoint}/chat/completions"
    print(f"🤖 Probando endpoint de chat completions: {url}")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.azure_ai_key}',
        'User-Agent': 'Atomia-Test/1.0'
    }
    
    payload = {
        "model": config.azure_ai_model,
        "messages": [
            {"role": "user", "content": "Test connection"}
        ],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Respuesta exitosa: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Detalles del error: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Texto de respuesta: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecuta todos los tests de diagnóstico"""
    print("=" * 60)
    print("🔧 DIAGNÓSTICO DE CONECTIVIDAD AZURE AI")
    print("=" * 60)
    
    print(f"📋 Configuración:")
    print(f"   Endpoint: {config.azure_ai_endpoint}")
    print(f"   Modelo: {config.azure_ai_model}")
    print(f"   Key configurada: {'✅' if config.azure_ai_key else '❌'}")
    print()
    
    # Test 1: DNS
    dns_ok = test_dns_resolution()
    print()
    
    # Test 2: Conectividad básica
    if dns_ok:
        http_ok = test_basic_connectivity()
        print()
        
        # Test 3: Endpoint específico
        if http_ok:
            chat_ok = test_chat_completions_endpoint()
            print()
            
            if chat_ok:
                print("🎉 ¡TODOS LOS TESTS PASARON! Azure AI está funcionando correctamente.")
            else:
                print("⚠️  El endpoint básico funciona pero hay problemas con chat completions.")
        else:
            print("⚠️  Problemas de conectividad HTTP básica.")
    else:
        print("⚠️  Problemas de resolución DNS. Verifica el endpoint.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 