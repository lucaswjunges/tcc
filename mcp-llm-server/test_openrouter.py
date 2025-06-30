#!/usr/bin/env python3
"""
Teste específico do OpenRouter com diferentes modelos.
"""

import os
from dotenv import load_dotenv
load_dotenv('.env')

import openai

def test_openrouter_models():
    """Testa diferentes modelos do OpenRouter."""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ API key do OpenRouter não encontrada")
        return
    
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    # Lista de modelos para testar
    models_to_test = [
        "openai/gpt-3.5-turbo",
        "anthropic/claude-3-haiku",
        "google/gemini-pro",
        "microsoft/wizardlm-2-8x22b",
        "meta-llama/llama-3-8b-instruct:free"
    ]
    
    print("🔄 Testando modelos do OpenRouter...")
    
    working_models = []
    for model in models_to_test:
        try:
            print(f"\n🧪 Testando {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Diga apenas 'Olá'"}],
                max_tokens=10
            )
            result = response.choices[0].message.content
            print(f"✅ {model}: {result}")
            working_models.append(model)
            
        except Exception as e:
            print(f"❌ {model}: {str(e)}")
    
    print(f"\n📊 Resultado: {len(working_models)}/{len(models_to_test)} modelos funcionando")
    print("✅ Modelos que funcionam:")
    for model in working_models:
        print(f"   - {model}")
    
    return working_models[0] if working_models else None

if __name__ == "__main__":
    working_model = test_openrouter_models()
    if working_model:
        print(f"\n💡 Use este modelo no servidor: {working_model}")
    else:
        print("\n⚠️  Nenhum modelo funcionou. Verifique sua conta OpenRouter.")