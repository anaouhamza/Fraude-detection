from flask import Flask, render_template, request, flash, jsonify
import numpy as np
import pandas as pd
import mysql.connector
import joblib

app = Flask(__name__)
app.secret_key = "tawfiqsudine212"

# Chargement du modèle de détection de fraude
model = joblib.load("modele_fraud_detection.joblib")

# Connexion à la base de données MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="signup2",
    port="3307"
)
cursor = conn.cursor()

#appel de la datafrme de training pour  formaliser les données en entrée
df = pd.read_csv("C:/data.csv")
df = df.drop(columns="PolicyNumber")
df.Age = df.Age.replace(0, 16)
mask_holder2 = df["AgeOfPolicyHolder"] != "16 to 17"
df = df[mask_holder2]
df = df.drop(columns="PolicyType")
df = pd.get_dummies(df, columns=['Month', 'WeekOfMonth', 'DayOfWeek', 'Make', 'AccidentArea', 'DayOfWeekClaimed', 'MonthClaimed',
                                 'WeekOfMonthClaimed', 'Sex', 'MaritalStatus', 'Fault', 'VehicleCategory', 'VehiclePrice', 'RepNumber',
                                 'DriverRating', 'Days_Policy_Accident', 'Days_Policy_Claim', 'PastNumberOfClaims', 'AgeOfVehicle',
                                 'AgeOfPolicyHolder', 'PoliceReportFiled', 'WitnessPresent', 'AgentType', 'NumberOfSuppliments',
                                 'AddressChange_Claim', 'NumberOfCars', 'Year', 'BasePolicy'],
                    drop_first=True)

X=df.drop(columns=['FraudFound_P'])

#creer dataframe avec les mme colonne de X mais nulle
dataframe_zero = pd.DataFrame(0, index=range(len(X)), columns=X.columns)

@app.route("/verify")
def index():
    flash("Auto Insurance Fraud Detection")
    return render_template("index.html")

@app.route("/check", methods=["POST", "GET"])
def fraud_test():
    # Récupérer le client_id depuis le formulaire
    client_id = request.form['input_id']

    # Récupérer les paramètres depuis la base de données pour le client_id donné
    cursor.execute('''
        SELECT Month, WeekOfMonth, DayOfWeek, Make, AccidentArea, DayOfWeekClaimed, MonthClaimed, WeekOfMonthClaimed, Sex,MaritalStatus,Age,
                Fault, VehicleCategory, VehiclePrice , RepNumber, Deductible, DriverRating, Days_Policy_Accident, Days_Policy_Claim, PastNumberOfClaims, AgeOfVehicle,
             AgeOfPolicyHolder, PoliceReportFiled, WitnessPresent,AgentType,  NumberOfSuppliments, AddressChange_Claim, NumberOfCars, Year, BasePolicy FROM dbreclamation2 WHERE id = %s''', (client_id,))
    latest_params = cursor.fetchone()

    # Vérification si des données ont été récupérées
    if latest_params is not None:
        # Créer un dataframe avec les paramètres récupérés
        colonnes = ["Month", "WeekOfMonth", "DayOfWeek", "Make", "AccidentArea", "DayOfWeekClaimed", "MonthClaimed", "WeekOfMonthClaimed", "Sex","MaritalStatus","Age",
                "Fault", "VehicleCategory", "VehiclePrice" , "RepNumber", "Deductible", "DriverRating", "Days_Policy_Accident", "Days_Policy_Claim", "PastNumberOfClaims", "AgeOfVehicle",
             "AgeOfPolicyHolder", "PoliceReportFiled", "WitnessPresent","AgentType",  "NumberOfSuppliments", "AddressChange_Claim", "NumberOfCars", "Year", "BasePolicy"]

        latest_params_df = pd.DataFrame([latest_params], columns=colonnes)
        latest_params_df = pd.get_dummies(latest_params_df, columns=['Month', 'WeekOfMonth', 'DayOfWeek', 'Make', 'AccidentArea', 'DayOfWeekClaimed', 'MonthClaimed',
                                     'WeekOfMonthClaimed', 'Sex', 'MaritalStatus', 'Fault', 'VehicleCategory', 'VehiclePrice', 'RepNumber',
                                     'DriverRating', 'Days_Policy_Accident', 'Days_Policy_Claim', 'PastNumberOfClaims', 'AgeOfVehicle',
                                     'AgeOfPolicyHolder', 'PoliceReportFiled', 'WitnessPresent', 'AgentType', 'NumberOfSuppliments',
                                     'AddressChange_Claim', 'NumberOfCars', 'Year', 'BasePolicy'],drop_first=False)

        # Créer une liste des colonnes communes entre dataframe_zero et latest_params_df
        colonnes_communes = dataframe_zero.columns.intersection(latest_params_df.columns)

        # Mettre à jour dataframe_zero avec les valeurs de latest_params_df pour les colonnes communes
        for c in colonnes_communes:
            dataframe_zero[c] = latest_params_df[c].astype(int)

        # Appliquer le modèle de détection de fraude
        is_fraudulent = model.predict(dataframe_zero)

        if is_fraudulent[0] == 1:
            flash(f"The client with id {client_id} is flagged for fraud!")
        else:
            flash(f"No fraud detected for the client with id {client_id}")

    else:
        flash(f"No data found for the client with id {client_id}")

    return render_template("index.html")

@app.route("/fetch_test")
def get_results():
    # Exécuter une requête SQL pour obtenir tous les résultats de la base de données
    cursor.execute('SELECT * FROM dbreclamation2')
    results = cursor.fetchall()

    # Convertir les résultats en une liste de dictionnaires
    result_list = [dict(zip(cursor.column_names, row)) for row in results]

    # Retourner les résultats en format JSON
    return jsonify(result_list)

if __name__ == "__main__":
    app.run(debug=True)
