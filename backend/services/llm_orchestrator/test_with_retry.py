#!/usr/bin/env python3
import requests
import time
from src.config import config

def test_azure_ai_with_retry():
    """Test con reintentos para manejar problemas intermitentes de DNS"""
    url = f"{config.azure_ai_endpoint}/chat/completions"
    print(f"🚀 Probando Azure AI con reintentos...")
    print(f"URL: {url}")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {config.azure_ai_key}'
    }
    
    payload = {
        "model": config.azure_ai_model,
        "messages": [
            {"role": "user", "content": "¿Cuánto es 2+2?"}
        ],
        "max_tokens": 50
    }
    
    for attempt in range(5):
        try:
            print(f"📡 Intento {attempt + 1}/5...")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=30
            )
            
            print(f"✅ Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"🎉 ¡ÉXITO! Respuesta: {content}")
                return True
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"Respuesta: {response.text[:300]}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"🔄 Error de conexión en intento {attempt + 1}: {str(e)[:100]}...")
            if attempt < 4:
                print(f"⏳ Esperando 3 segundos antes del siguiente intento...")
                time.sleep(3)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            break
    
    print("❌ Todos los intentos fallaron")
    return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 TEST AZURE AI CON REINTENTOS")
    print("=" * 70)
    test_azure_ai_with_retry()
    print("=" * 70)
