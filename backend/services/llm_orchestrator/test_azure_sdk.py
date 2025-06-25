#!/usr/bin/env python3
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from src.config import config

def test_with_azure_sdk():
    """Test usando el SDK oficial de Azure AI"""
    print("🧪 Probando con Azure AI Inference SDK...")
    
    try:
        # Crear cliente usando el SDK oficial
        client = ChatCompletionsClient(
            endpoint=config.azure_ai_endpoint,
            credential=AzureKeyCredential(config.azure_ai_key)
        )
        
        print(f"✅ Cliente creado exitosamente")
        print(f"Endpoint: {config.azure_ai_endpoint}")
        
        # Hacer petición de prueba
        response = client.complete(
            messages=[
                {"role": "user", "content": "¿Cuánto es 2+2? Responde brevemente."}
            ],
            model=config.azure_ai_model,
            max_tokens=50
        )
        
        print(f"✅ Respuesta recibida!")
        print(f"Modelo usado: {response.model}")
        
        if response.choices:
            content = response.choices[0].message.content
            print(f"🎉 Contenido: {content}")
            
            # Información de tokens
            if hasattr(response, 'usage'):
                print(f"📊 Tokens usados: {response.usage.total_tokens}")
            
            return True
        else:
            print("❌ No se recibieron choices en la respuesta")
            return False
            
    except Exception as e:
        print(f"❌ Error con SDK: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔧 TEST CON AZURE AI INFERENCE SDK")
    print("=" * 70)
    success = test_with_azure_sdk()
    print("=" * 70)
    if success:
        print("🎉 ¡AZURE AI ESTÁ FUNCIONANDO!")
    else:
        print("❌ Problema persistente con Azure AI")
