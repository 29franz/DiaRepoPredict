# app.py
from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
import traceback
import io
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load the model and scaler
try:
    with open('scaler (1).pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("✅ Scaler loaded successfully")
except Exception as e:
    print(f"❌ Error loading scaler: {str(e)}")
    scaler = None

try:
    with open('logistic_model (1).pkl', 'rb') as f:
        model = pickle.load(f)
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    model = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or scaler is None:
        return jsonify({'error': 'Model not loaded properly'}), 500
    
    try:
        # Get data from request
        data = request.json
        
        # Validate required fields
        required_fields = [
            'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400
        
        # Convert all inputs to float
        try:
            features = [
                float(data['Pregnancies']),
                float(data['Glucose']),
                float(data['BloodPressure']),
                float(data['SkinThickness']),
                float(data['Insulin']),
                float(data['BMI']),
                float(data['DiabetesPedigreeFunction']),
                float(data['Age'])
            ]
        except ValueError as e:
            return jsonify({'error': f'Invalid input format: {str(e)}'}), 400
        
        # Convert to numpy array and reshape
        features_array = np.array(features).reshape(1, -1)
        
        # Scale the features
        scaled_features = scaler.transform(features_array)
        
        # Make prediction
        prediction = model.predict(scaled_features)
        probability = model.predict_proba(scaled_features)
        
        # Calculate risk level
        risk_percentage = probability[0][1] * 100
        if risk_percentage < 30:
            risk_level = "Low"
            risk_color = "green"
        elif risk_percentage < 60:
            risk_level = "Moderate"
            risk_color = "orange"
        else:
            risk_level = "High"
            risk_color = "red"
        
        # Prepare response
        result = {
            'success': True,
            'prediction': int(prediction[0]),
            'prediction_label': 'Diabetic' if prediction[0] == 1 else 'Non-Diabetic',
            'probability': float(probability[0][1]),
            'probability_percentage': float(risk_percentage),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'message': f'{"High risk of diabetes" if prediction[0] == 1 else "Low risk of diabetes"} detected',
            'detailed_message': f'Prediction: {"Diabetic" if prediction[0] == 1 else "Non-Diabetic"} with {risk_percentage:.1f}% probability ({risk_level} risk)',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Prediction error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    if model is None or scaler is None:
        return jsonify({'error': 'Model not loaded properly'}), 500
    
    try:
        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read CSV file
        try:
            df = pd.read_csv(file)
            original_columns = df.columns.tolist()
        except Exception as e:
            return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400
        
        # Check required columns
        required_columns = [
            'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'Missing columns: {", ".join(missing_columns)}'}), 400
        
        # Extract features
        features = df[required_columns].values
        
        # Scale features
        scaled_features = scaler.transform(features)
        
        # Make predictions
        predictions = model.predict(scaled_features)
        probabilities = model.predict_proba(scaled_features)
        
        # Calculate risk levels for each record
        risk_levels = []
        risk_colors = []
        for prob in probabilities[:, 1]:
            risk_percentage = prob * 100
            if risk_percentage < 30:
                risk_levels.append("Low")
                risk_colors.append("green")
            elif risk_percentage < 60:
                risk_levels.append("Moderate")
                risk_colors.append("orange")
            else:
                risk_levels.append("High")
                risk_colors.append("red")
        
        # Add results to dataframe
        df['Prediction'] = predictions
        df['Prediction_Label'] = ['Diabetic' if p == 1 else 'Non-Diabetic' for p in predictions]
        df['Probability'] = probabilities[:, 1]
        df['Probability_Percentage'] = probabilities[:, 1] * 100
        df['Risk_Level'] = risk_levels
        df['Risk_Color'] = risk_colors
        
        # Add detailed message for each record
        df['Message'] = df.apply(lambda row: 
            f'{"High risk of diabetes" if row["Prediction"] == 1 else "Low risk of diabetes"} ({row["Risk_Level"]})', 
            axis=1)
        
        # Prepare CSV for download (with all original columns + predictions)
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        csv_data = output.getvalue().decode('utf-8')
        
        # Prepare sample data for display
        sample_data = df.head(10).to_dict('records')
        
        # Calculate statistics
        diabetic_count = int(predictions.sum())
        non_diabetic_count = int(len(predictions) - predictions.sum())
        diabetic_rate = (diabetic_count / len(predictions)) * 100
        
        # Calculate risk distribution
        risk_distribution = {
            'High': int(sum(1 for rl in risk_levels if rl == 'High')),
            'Moderate': int(sum(1 for rl in risk_levels if rl == 'Moderate')),
            'Low': int(sum(1 for rl in risk_levels if rl == 'Low'))
        }
        
        return jsonify({
            'success': True,
            'message': f'✅ Processed {len(df)} records successfully',
            'count': len(df),
            'diabetic_count': diabetic_count,
            'non_diabetic_count': non_diabetic_count,
            'diabetic_rate': float(diabetic_rate),
            'risk_distribution': risk_distribution,
            'sample_data': sample_data,
            'csv_data': csv_data,
            'filename': f'diabetes_predictions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        app.logger.error(f"Batch prediction error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/download_results', methods=['POST'])
def download_results():
    try:
        data = request.json.get('csv_data')
        filename = request.json.get('filename', 'diabetes_predictions.csv')
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create response with CSV data
        response = Response(
            data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response
    
    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': f'Download error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    status = {
        'status': 'healthy' if model is not None and scaler is not None else 'unhealthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(status)

@app.route('/features', methods=['GET'])
def features():
    feature_info = {
        'features': [
            {'name': 'Pregnancies', 'type': 'integer', 'min': 0, 'max': 20, 'description': 'Number of pregnancies'},
            {'name': 'Glucose', 'type': 'integer', 'min': 0, 'max': 300, 'description': 'Glucose concentration in mg/dL'},
            {'name': 'BloodPressure', 'type': 'integer', 'min': 0, 'max': 150, 'description': 'Blood pressure in mm Hg'},
            {'name': 'SkinThickness', 'type': 'integer', 'min': 0, 'max': 100, 'description': 'Skin thickness in mm'},
            {'name': 'Insulin', 'type': 'integer', 'min': 0, 'max': 900, 'description': 'Insulin level in mu U/ml'},
            {'name': 'BMI', 'type': 'float', 'min': 0, 'max': 70, 'description': 'Body Mass Index'},
            {'name': 'DiabetesPedigreeFunction', 'type': 'integer', 'min': 0, 'max': 10, 'description': 'Genetic risk score (whole number)'},
            {'name': 'Age', 'type': 'integer', 'min': 0, 'max': 120, 'description': 'Age in years'}
        ],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(feature_info)

if __name__ == '__main__':
    if model is None or scaler is None:
        print("WARNING: Model or scaler not loaded properly!")
        print("Make sure the .pkl files are in the correct directory.")
    else:
        print("Application ready!")
        print(f"Model: {'Loaded' if model else 'Not loaded'}")
        print(f"Scaler: {'Loaded' if scaler else 'Not loaded'}")
    

    # app.run(debug=True, host='0.0.0.0', port=5000)
