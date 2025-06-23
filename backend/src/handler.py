import json
import os
import boto3
import pymysql
from decimal import Decimal

# Initialisation du client Secrets Manager
secrets_manager = boto3.client('secretsmanager')

# Cache pour la configuration de la base de données
db_config = None


def get_db_config():
    """Récupère la configuration de la base de données depuis AWS Secrets Manager."""
    global db_config
    if db_config is None:
        secret_arn = os.environ['DB_SECRET_ARN']
        secret = secrets_manager.get_secret_value(SecretId=secret_arn)
        db_config = json.loads(secret['SecretString'])
    return db_config


def calculate_imc(height, weight):
    """Calcule l'IMC (Indice de Masse Corporelle) à partir de la taille et du poids."""
    return round(weight / (height * height), 2)


def decimal_to_float(obj):
    """Convertit les objets Decimal en float pour la sérialisation JSON."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    """Point d'entrée pour la fonction Lambda."""
    try:
        # Obtenir la configuration de la base de données
        config = get_db_config()
        
        # Connexion à la base de données
        connection = pymysql.connect(
            host=config['host'],
            user=config['username'],
            password=config['password'],
            database=config['dbname'],
            cursorclass=pymysql.cursors.DictCursor
        )

        http_method = event.get('httpMethod')
        path = event.get('path')

        with connection.cursor() as cursor:
            if http_method == 'POST' and path == '/imc':
                body = json.loads(event.get('body', '{}'))
                height = body.get('height')
                weight = body.get('weight')

                if not height or not weight or height <= 0 or weight <= 0:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({
                            'error': 'Taille et poids doivent être des nombres positifs'
                        })
                    }

                imc = calculate_imc(height, weight)

                # Insérer dans la base de données
                cursor.execute(
                    'INSERT INTO imc_history (height, weight, imc) VALUES (%s, %s, %s)',
                    (height, weight, imc)
                )
                connection.commit()

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'imc': imc,
                        'message': 'IMC calculé et sauvegardé avec succès'
                    })
                }

            elif http_method == 'GET' and path == '/imc':
                cursor.execute('SELECT * FROM imc_history ORDER BY created_at DESC')
                results = cursor.fetchall()

                return {
                    'statusCode': 200,
                    'body': json.dumps(results, default=decimal_to_float)
                }

            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Route non trouvée'})
                }

    except Exception as e:
        print(f'Erreur: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erreur serveur'})
        }
    finally:
        if 'connection' in locals():
            connection.close()