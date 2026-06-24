import numpy as np
from sklearn.ensemble import IsolationForest

class SecurityML:
    def __init__(self):
        # Données de référence "Ultra-Normales"
        X_train = [[5, 0, 0], [10, 0, 0], [15, 0, 0], [20, 0, 0]]
        # Contamination à 0.01 : tout ce qui s'éloigne un peu est une anomalie
        self.model = IsolationForest(contamination=0.01, random_state=42)
        self.model.fit(X_train)

    def analyze_request(self, features):
        data = np.array([features])
        # Si la requête contient des caractères spéciaux (features[1] ou [2] > 0), 
        # on force le statut anomalie même si le ML hésite.
        if features[1] > 0 or features[2] > 0:
            return 1
            
        prediction = self.model.predict(data)
        return 1 if prediction[0] == -1 else 0