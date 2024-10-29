import logging
from typing import Dict, Optional
import numpy as np
from typing import List


logger = logging.getLogger(__name__)

class RiskCalculator:
    def __init__(self):
        # Base weights for different risk factors
        self.INSURANCE_WEIGHTS = {
            'age': 0.2,
            'bmi': 0.15,
            'smoking': 0.25,
            'exercise': 0.15,
            'medical_history': 0.25
        }
        
        self.DIABETES_WEIGHTS = {
            'age': 0.15,
            'bmi': 0.2,
            'family_history': 0.25,
            'exercise': 0.2,
            'diet': 0.2
        }

    def calculate_insurance_risk(self, user_data: Dict) -> float:
        """Calculate insurance risk score based on user data"""
        try:
            risk_score = 0.0
            
            # Age risk
            age = int(user_data.get('age', 0))
            age_risk = self._calculate_age_risk(age)
            
            # BMI risk
            height_m = float(user_data.get('height', 0)) / 100  # convert to meters
            weight_kg = float(user_data.get('weight', 0))
            bmi_risk = self._calculate_bmi_risk(height_m, weight_kg)
            
            # Lifestyle risks
            lifestyle = user_data.get('lifestyle_factors', {})
            smoking_risk = self._calculate_smoking_risk(lifestyle.get('smoking_status'))
            exercise_risk = self._calculate_exercise_risk(lifestyle.get('exercise_frequency'))
            
            # Medical history risk
            medical_risk = self._calculate_medical_risk(user_data.get('medical_history', {}))
            
            # Calculate weighted risk score
            risk_score = (
                age_risk * self.INSURANCE_WEIGHTS['age'] +
                bmi_risk * self.INSURANCE_WEIGHTS['bmi'] +
                smoking_risk * self.INSURANCE_WEIGHTS['smoking'] +
                exercise_risk * self.INSURANCE_WEIGHTS['exercise'] +
                medical_risk * self.INSURANCE_WEIGHTS['medical_history']
            )
            
            return min(max(risk_score, 0), 1)  # Normalize between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating insurance risk: {str(e)}")
            return 0.5  # Default risk score

    def calculate_diabetes_risk(self, user_data: Dict) -> float:
        """Calculate diabetes risk score based on user data"""
        try:
            risk_score = 0.0
            
            # Age risk
            age = int(user_data.get('age', 0))
            age_risk = self._calculate_age_risk(age, diabetes_context=True)
            
            # BMI risk
            height_m = float(user_data.get('height', 0)) / 100
            weight_kg = float(user_data.get('weight', 0))
            bmi_risk = self._calculate_bmi_risk(height_m, weight_kg)
            
            # Lifestyle risks
            lifestyle = user_data.get('lifestyle_factors', {})
            exercise_risk = self._calculate_exercise_risk(lifestyle.get('exercise_frequency'))
            diet_risk = self._calculate_diet_risk(lifestyle.get('diet_type'))
            
            # Family history risk
            medical = user_data.get('medical_history', {})
            family_risk = self._calculate_family_risk(medical.get('conditions', []))
            
            # Calculate weighted risk score
            risk_score = (
                age_risk * self.DIABETES_WEIGHTS['age'] +
                bmi_risk * self.DIABETES_WEIGHTS['bmi'] +
                family_risk * self.DIABETES_WEIGHTS['family_history'] +
                exercise_risk * self.DIABETES_WEIGHTS['exercise'] +
                diet_risk * self.DIABETES_WEIGHTS['diet']
            )
            
            return min(max(risk_score, 0), 1)  # Normalize between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating diabetes risk: {str(e)}")
            return 0.5  # Default risk score

    def _calculate_age_risk(self, age: int, diabetes_context: bool = False) -> float:
        """Calculate age-related risk"""
        if diabetes_context:
            if age > 65: return 1.0
            elif age > 45: return 0.7
            elif age > 35: return 0.4
            return 0.2
        else:
            if age > 70: return 1.0
            elif age > 50: return 0.7
            elif age > 30: return 0.4
            return 0.2

    def _calculate_bmi_risk(self, height_m: float, weight_kg: float) -> float:
        """Calculate BMI-related risk"""
        try:
            if height_m <= 0: return 0.5
            bmi = weight_kg / (height_m * height_m)
            if bmi > 35: return 1.0
            elif bmi > 30: return 0.8
            elif bmi > 25: return 0.6
            elif bmi < 18.5: return 0.4
            return 0.2
        except:
            return 0.5

    def _calculate_smoking_risk(self, smoking_status: Optional[str]) -> float:
        """Calculate smoking-related risk"""
        if not smoking_status:
            return 0.5
        status_map = {
            'current': 1.0,
            'former': 0.6,
            'never': 0.1
        }
        return status_map.get(smoking_status.lower(), 0.5)

    def _calculate_exercise_risk(self, exercise_frequency: Optional[str]) -> float:
        """Calculate exercise-related risk"""
        if not exercise_frequency:
            return 0.5
        frequency_map = {
            'never': 1.0,
            'rarely': 0.8,
            'sometimes': 0.6,
            'regularly': 0.3,
            'daily': 0.1
        }
        return frequency_map.get(exercise_frequency.lower(), 0.5)

    def _calculate_diet_risk(self, diet_type: Optional[str]) -> float:
        """Calculate diet-related risk"""
        if not diet_type:
            return 0.5
        diet_map = {
            'unhealthy': 1.0,
            'average': 0.5,
            'healthy': 0.2,
            'very_healthy': 0.1
        }
        return diet_map.get(diet_type.lower(), 0.5)

    def _calculate_medical_risk(self, medical_history: Dict) -> float:
        """Calculate medical history-related risk"""
        risk = 0.3  # Base risk
        conditions = medical_history.get('conditions', [])
        
        high_risk_conditions = ['heart disease', 'diabetes', 'cancer']
        medium_risk_conditions = ['hypertension', 'high cholesterol']
        
        for condition in conditions:
            condition = condition.lower().strip()
            if condition in high_risk_conditions:
                risk += 0.3
            elif condition in medium_risk_conditions:
                risk += 0.15
                
        return min(risk, 1.0)

    def _calculate_family_risk(self, conditions: List[str]) -> float:
        """Calculate family history-related risk"""
        risk = 0.2  # Base risk
        conditions = [c.lower().strip() for c in conditions]
        
        if 'diabetes' in conditions:
            risk += 0.4
        if 'heart disease' in conditions:
            risk += 0.2
            
        return min(risk, 1.0)

