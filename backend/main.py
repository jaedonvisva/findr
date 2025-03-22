from utils import *
from flask import Flask, request
from flask_cors import CORS
import jsonify
import tempfile

app = Flask(__name__)
CORS(app)

@app.route('/parse', methods=['POST'])
def parse():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    try:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, request.files['resume'].filename)
        request.files['resume'].save(temp_path)
        parsed_resume = parse_resume(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(parsed_resume)

@app.route('/create_user', methods=['POST'])
def createuser():
    email = request.json["email"]
    return create_user(request.json["parsed_resume"], email)

@app.route('/remove_match', methods=['POST'])
def removematch():
    user1, user2 = request.json["user1"], request.json["user2"]
    return remove_match(user1, user2)
    
@app.route('/get_matches', methods=['POST'])
def get_matches_for_user():
    user_id = request.json["user_id"]
    return get_matches(user_id)

@app.route('/like', methods=['POST'])
def like():
    user1, user2 = request.json["user1"], request.json["user2"]
    like_user(user1, user2)
    return jsonify({"message": "Like created"})

if __name__ == '__main__':
    app.run(debug=True)