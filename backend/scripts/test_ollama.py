# backend/scripts/test_ollama.py
import httpx
import time
import sys
import json

def test_ollama_connection():
    """Test la connexion à Ollama et mesure la latence"""
    
    print("🔍 Test de connexion à Ollama...")
    print("=" * 50)
    
    # Configuration
    OLLAMA_URL = "http://localhost:11434/api/chat"
    MODEL = "smollm:135m"  # Version ultra-légère pour une meilleure latence
    
    # Payload de test
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Tu es un assistant utile et concis."},
            {"role": "user", "content": "bonjour, réponds en une phrase"}
        ],
        "stream": False,
        "options": {
            "num_predict": 50,  # Limite la longueur de la réponse
            "temperature": 0.7
        }
    }
    
    try:
        # Mesure du temps de réponse
        start_time = time.time()
        
        # Appel à Ollama
        with httpx.Client(timeout=30.0) as client:
            response = client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Affichage des résultats
        print(f"✅ Connexion réussie à Ollama ({MODEL})")
        print(f"⏱️  Temps de réponse : {elapsed_time:.2f} secondes")
        print("\n📝 Réponse brute :")
        print("-" * 50)
        
        # Affichage formaté de la réponse
        try:
            data = response.json()
            if 'message' in data and 'content' in data['message']:
                print(data['message']['content'])
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
        
        print("-" * 50)
        
        # Statistiques supplémentaires
        print(f"\n📊 Statistiques :")
        print(f"   - Modèle : {MODEL}")
        print(f"   - Temps de réponse : {elapsed_time:.2f}s")
        
        # Analyse de la latence
        if elapsed_time > 8.0:
            print(f"\n⚠️  ATTENTION : Latence élevée ({elapsed_time:.2f}s > 8s)")
            print("💡 Suggestion : Utiliser un modèle encore plus petit")
            print("   ou prévoir un fallback API dès le Checkpoint #1")
        elif elapsed_time > 5.0:
            print(f"\n⚡ Latence acceptable mais élevée ({elapsed_time:.2f}s)")
            print("💡 Considérer le fallback API si nécessaire")
        elif elapsed_time > 3.0:
            print(f"\n✅ Bonne latence ({elapsed_time:.2f}s) - Adapté pour la démo")
        else:
            print(f"\n🚀 Latence excellente ({elapsed_time:.2f}s) - Parfait pour la démo live")
            
        return True, elapsed_time
        
    except httpx.ConnectError:
        print("❌ ERREUR : Impossible de se connecter à Ollama")
        print("\n📋 Instructions d'installation :")
        print("1. Ollama n'est pas installé ou pas lancé")
        print("2. Dans un terminal, lancez : ollama serve")
        print("3. Dans un autre terminal, téléchargez le modèle : ollama pull gemma4:e2b")
        print("4. Vérifiez que le port 11434 est disponible")
        print("\n📚 Documentation : https://ollama.com/download")
        return False, 0
        
    except httpx.TimeoutException:
        print("❌ ERREUR : Timeout - Ollama met trop de temps à répondre")
        print("💡 Essayez un modèle encore plus petit")
        return False, 0
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"❌ ERREUR : Modèle '{MODEL}' non trouvé")
            print(f"\n📋 Pour installer le modèle :")
            print(f"   ollama pull {MODEL}")
            print(f"\n💡 Note : Vérifiez que le modèle 'gemma4:e2b' existe")
            print("   Si ce n'est pas le cas, essayez :")
            print("   - gemma3:2b (équivalent léger)")
            print("   - gemma3:4b (équivalent moyen)")
            print("   - gemma3 (version complète)")
        else:
            print(f"❌ ERREUR HTTP {e.response.status_code}: {e.response.text}")
        return False, 0
        
    except Exception as e:
        print(f"❌ ERREUR inattendue : {str(e)}")
        return False, 0

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 Test de l'étape 1 - Setup Ollama (gemma4:e2b)")
    print("=" * 50 + "\n")
    
    success, latency = test_ollama_connection()
    
    if success:
        print("\n✨ Test réussi ! Vous pouvez passer à l'étape suivante.")
        print(f"   Latence mesurée : {latency:.2f}s")
        sys.exit(0)
    else:
        print("\n❌ Échec du test. Résolvez les problèmes avant de continuer.")
        sys.exit(1)