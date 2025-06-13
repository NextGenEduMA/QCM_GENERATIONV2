# Générateur de QCM Arabe avec RAG

## Description
Application pour générer automatiquement des questionnaires à choix multiples (QCM) à partir de textes en arabe en utilisant la technologie RAG (Retrieval Augmented Generation).

## Technologies Utilisées
- **FastAPI**: Framework web rapide pour créer des API avec Python
- **OpenAI API**: Génération de questions intelligentes avec GPT-4o Mini
- **RAG (Retrieval Augmented Generation)**: Technique qui améliore la génération de texte en récupérant des informations pertinentes
- **FAISS**: Bibliothèque pour la recherche efficace de similarité vectorielle
- **Sentence Transformers**: Modèles pour créer des embeddings de texte multilingues
- **PyPDF2**: Extraction de texte à partir de fichiers PDF
- **MongoDB**: Stockage persistant des QCMs générés

## Architecture
L'application utilise une architecture RAG (Retrieval Augmented Generation):
1. **Indexation**: Les documents PDF sont traités et indexés avec FAISS
2. **Récupération**: Pour une requête donnée, les passages les plus pertinents sont récupérés
3. **Génération**: OpenAI génère des QCMs basés sur les passages récupérés
4. diagram de notre architecture :
   ![Image](https://github.com/user-attachments/assets/7a0ee10a-8ccf-49f1-980d-4c1701dca465)

## Installation
```
pip install -r requirements-all.txt
```

## Configuration
1. Créez un fichier `.env` basé sur `.env.example`
2. Ajoutez votre clé API OpenAI: `OPENAI_API_KEY=votre-clé-api`

## Utilisation
Pour lancer l'application web:
```
python -m uvicorn simple_app:app --host 127.0.0.1 --port 8001
```

Ou utilisez le fichier batch:
```
run_simple_app.bat
```

## Workflow
1. **Téléchargement de PDF**: Téléchargez un document PDF en arabe
2. **Indexation**: Le système indexe automatiquement le contenu du PDF
3. **Requête**: Entrez une requête ou un sujet pour générer des questions
4. **Génération de QCM**: Le système utilise RAG pour générer des QCMs pertinents
5. **Sauvegarde**: Les QCMs peuvent être sauvegardés dans MongoDB et exportés en JSON

## Structure du Projet
- `simple_app.py`: Application principale FastAPI
- `arabic_diacritized_qcm_v3.py`: Générateur de QCM avec support RAG
- `embedding.py`: Module pour créer et gérer les embeddings de texte
- `retriever.py`: Module pour récupérer les passages pertinents
- `models.py`: Modèles de données
- `db.py`: Opérations de base de données

## Fonctionnalités Avancées
- Support des textes arabes avec diacritiques
- Amélioration automatique des questions générées
- Interface web réactive
- Stockage persistant des résultats
- Sélection de paragraphes spécifiques pour la génération
