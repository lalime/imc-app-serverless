import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Remplacer par l'URL de votre API Gateway après déploiement
API_URL = "https://your-api-id.execute-api.region.amazonaws.com/Prod"

st.title("Calculateur d'IMC")

# Formulaire pour calculer l'IMC
with st.form("imc_form"):
    height = st.number_input("Taille (m)", min_value=0.1, value=1.75, step=0.01)
    weight = st.number_input("Poids (kg)", min_value=0.1, value=70.0, step=0.1)
    submitted = st.form_submit_button("Calculer l'IMC")

if submitted:
    try:
        response = requests.post(
            f"{API_URL}/imc",
            json={"height": height, "weight": weight},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"Votre IMC est : {result['bmi']}")
        st.write(result['message'])
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors du calcul de l'IMC : {str(e)}")

# Afficher l'historique
st.subheader("Historique des calculs")
try:
    response = requests.get(f"{API_URL}/imc")
    response.raise_for_status()
    history = response.json()
    if history:
        df = pd.DataFrame(history)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        st.dataframe(
            df[['height', 'weight', 'bmi', 'created_at']],
            column_config={
                "height": "Taille (m)",
                "weight": "Poids (kg)",
                "bmi": "IMC",
                "created_at": "Date"
            }
        )
    else:
        st.info("Aucun historique disponible.")
except requests.exceptions.RequestException as e:
    st.error(f"Erreur lors de la récupération de l'historique : {str(e)}")