from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import insightface
import io

app = Flask(__name__)
CORS(app)

model = insightface.app.FaceAnalysis(name='buffalo_l')
model.prepare(ctx_id=0, det_size=(640, 640))

@app.route('/embed', methods=['POST'])
def get_embedding():
    if 'image' not in request.files:
        return jsonify({'error': 'Image file missing'}), 400

    file = request.files['image']
    img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    faces = model.get(img)
    if not faces:
        return jsonify({'error': 'No face detected'}), 400

    embedding = faces[0].embedding.tolist()
    return jsonify({'embedding': embedding})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
