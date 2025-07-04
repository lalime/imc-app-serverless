# Application Serverless AWS pour le Calcul de l'IMC

Cette application serverless utilise AWS pour calculer l'Indice de Masse Corporelle (IMC) et stocker l'historique des calculs dans une base de données MySQL Aurora Serverless. Elle inclut un backend construit avec **AWS Serverless Application Model (SAM)**, **AWS Lambda** (en Python), **Amazon API Gateway**, et un frontend Python utilisant **Streamlit** pour afficher un calculateur d'IMC et l'historique.

## Architecture

### Backend
- **Amazon API Gateway** : Fournit une API REST (POST `/imc` pour calculer et sauvegarder l'IMC, GET `/imc` pour récupérer l'historique).
- **AWS Lambda** : Exécute la logique métier en Python (calcul de l'IMC et interaction avec la base de données).
- **Amazon Aurora Serverless (MySQL)** : Stocke l'historique des calculs d'IMC.
- **AWS Secrets Manager** : Gère les identifiants de la base de données.
- **AWS SAM** : Simplifie le déploiement des ressources serverless.

### Frontend
- **Streamlit** : Application Python pour saisir la taille et le poids, calculer l'IMC, et afficher l'historique via l'API.

## Prérequis

### Backend
- [AWS CLI](https://aws.amazon.com/cli/) configuré (`aws configure`).
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html).
- [Python](https://www.python.org/) (version 3.8 ou supérieure).
- [Git](https://git-scm.com/).
- Compte AWS avec permissions pour Lambda, API Gateway, Aurora, Secrets Manager, IAM.

### Frontend
- [Python](https://www.python.org/) (version 3.8 ou supérieure).
- [Streamlit](https://streamlit.io/) (`pip install streamlit`).
- [Requests](https://docs.python-requests.org/) (`pip install requests`).

## Structure du Projet

```plaintext
imc-app-serverless/
├── backend/
│   ├── events/
│   │   └── event.json           # Exemple d'événement pour tester localement
│   ├── src/
│   │   └── handler.py          # Code de la fonction Lambda
│   ├── tests/
│   │   └── unit/
│   │       └── test_handler.py # Tests unitaires
│   ├── requirements.txt        # Dépendances Python pour Lambda
│   └── template.yaml           # Modèle AWS SAM
├── frontend/
│   ├── app.py                  # Application Streamlit
│   └── requirements.txt        # Dépendances Python
├── README.md                   # Ce fichier
└── LICENSE                     # Licence MIT
```

## Configuration

### 1. Cloner le dépôt

```bash
git clone https://github.com/lalime/imc-app-serverless.git
cd imc-app-serverless
```

### 2. Configurer le Backend

#### a. Installer les dépendances Python

Créez un environnement virtuel et installez les dépendances pour le développement :

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
```

#### b. Configurer les variables d'environnement

Créez un fichier `.env` dans `backend/` :

```plaintext
DB_SECRET_ARN=arn:aws:secretsmanager:region:account-id:secret:your-secret
```

#### c. Configurer la base de données

1. **Créer un cluster Aurora Serverless** :
   - Dans la console AWS RDS, créez un cluster Aurora Serverless (MySQL 5.7 ou 8.0).
   - Notez l'endpoint (par exemple, `imcdb.cluster-xxxx.us-east-1.rds.amazonaws.com`).
   - Configurez le VPC et les groupes de sécurité pour l'accès Lambda.

2. **Créer la table `imc_history`** :

   ```sql
   CREATE DATABASE imcdb;
   USE imcdb;
   CREATE TABLE imc_history (
       id INT AUTO_INCREMENT PRIMARY KEY,
       height FLOAT NOT NULL,
       weight FLOAT NOT NULL,
       imc FLOAT NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Stocker les identifiants dans Secrets Manager** :
   - Créez un secret dans Secrets Manager (`aurora-credentials`) :

     ```json
     {
       "host": "your-aurora-endpoint",
       "username": "admin",
       "password": "your-password",
       "dbname": "imcdb"
     }
     ```

   - Notez l'ARN du secret.

### 3. Configurer le Frontend

#### a. Installer les dépendances Python

```bash
cd frontend
pip install -r requirements.txt
```

#### b. Configurer l'URL de l'API

Modifiez `frontend/app.py` pour inclure l'URL de votre API Gateway (obtenue après déploiement) :

```python
API_URL = "https://your-api-id.execute-api.region.amazonaws.com/Prod"
```

## Déploiement

### Backend

1. **Construire l'application**

```bash
cd backend
sam build
```

2. **Déployer sur AWS**

```bash
sam deploy --guided
```

- **Stack Name** : `imc-app-serverless-stack`.
- **AWS Region** : Par exemple, `us-east-1`.
- **Confirm changes before deploy** : Oui.
- **Allow SAM CLI IAM role creation** : Oui.

Notez l'URL de l'API Gateway dans la sortie (par exemple, `https://abc123.execute-api.us-east-1.amazonaws.com/Prod/`).

### Frontend

Exécutez l'application Streamlit localement :

```bash
cd frontend
streamlit run app.py
```

Accédez à l'application dans votre navigateur (`http://localhost:8501`).

## Utilisation

### Backend API

- **POST /imc** : Calcule et sauvegarde l'IMC.

```bash
curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/Prod/imc \
-H "Content-Type: application/json" \
-d '{"height": 1.75, "weight": 70}'
```

Réponse :

```json
{
  "imc": 22.86,
  "message": "IMC calculé et sauvegardé avec succès"
}
```

- **GET /imc** : Récupère l'historique.

```bash
curl https://abc123.execute-api.us-east-1.amazonaws.com/Prod/imc
```

Réponse :

```json
[
  {
    "id": 1,
    "height": 1.75,
    "weight": 70,
    "imc": 22.86,
    "created_at": "2025-06-23T05:46:32Z"
  }
]
```

### Frontend

1. Ouvrez l'application Streamlit (`http://localhost:8501`).
2. Saisissez votre taille (en mètres) et votre poids (en kg).
3. Cliquez sur "Calculer l'IMC" pour afficher le résultat et sauvegarder.
4. Consultez l'historique dans le tableau.

## Tester localement

### Backend

```bash
cd backend
sam local invoke ImcFunction --event events/event.json
```

Testez l'API :

```bash
sam local start-api
```

### Frontend

```bash
cd frontend
streamlit run app.py
```

## Nettoyage

### Backend

```bash
aws cloudformation delete-stack --stack-name imc-app-serverless-stack
```

Supprimez manuellement le cluster Aurora et le secret Secrets Manager.

### Frontend

Aucune ressource AWS, donc aucune suppression nécessaire.

## Dépannage

- **Backend** :
  - Erreur de connexion à la base : Vérifiez l'endpoint, les identifiants, et les groupes de sécurité.
  - Erreur d'autorisation : Vérifiez les permissions IAM de Lambda.
  - Consultez les logs CloudWatch (`/aws/lambda/ImcFunction`).
- **Frontend** :
  - Erreur de connexion à l'API : Vérifiez l'URL dans `app.py`.
  - Erreur d'affichage : Assurez-vous que Streamlit est installé.

## Contribuer

1. Forkez le dépôt.
2. Créez une branche (`git checkout -b feature/nouvelle-fonctionnalite`).
3. Commitez vos changements (`git commit -m "Ajout de la fonctionnalité"`).
4. Poussez la branche (`git push origin feature/nouvelle-fonctionnalite`).
5. Ouvrez une Pull Request.

## Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE).