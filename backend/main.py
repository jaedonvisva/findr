from utils import *
from flask import Flask, request
from flask_cors import CORS
import jsonify

app = Flask(__name__)
CORS(app)

@app.route('/parse', methods=['POST'])
def parse():
    resume_file = request.files['resume']
    parsed_resume = parse_resume(resume_file)
    create_user(parsed_resume)
    return parsed_resume

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