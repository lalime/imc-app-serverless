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
    global db_config
    if db_config is None:
        secret_arn = os.environ['DB_SECRET_ARN']
        secret = secrets_manager.get_secret_value(SecretId=secret_arn)
        db_config = json.loads(secret['SecretString'])
    return db_config

def calculate_bmi(height, weight):
    return round(weight / (height * height), 2)

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
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
            if http_method == 'POST' and path == '/bmi':
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

                bmi = calculate_bmi(height, weight)

                # Insérer dans la base de données
                cursor.execute(
                    'INSERT INTO bmi_history (height, weight, bmi) VALUES (%s, %s, %s)',
                    (height, weight, bmi)
                )
                connection.commit()

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'bmi': bmi,
                        'message': 'IMC calculé et sauvegardé avec succès'
                    })
                }

            elif http_method == 'GET' and path == '/bmi':
                cursor.execute('SELECT * FROM bmi_history ORDER BY created_at DESC')
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