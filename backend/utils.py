# Resume Parser
import cohere
import os
import pymongo
import PyPDF2
import json
import datetime
from bson import ObjectId


# COHERE_API = os.getenv("COHERE_API")
MONGO = "mongodb+srv://jaedonvisva2006:fiySIGcHsUtLB2Fj@cluster0.2nxyi.mongodb.net/?appName=Cluster0"
co = cohere.ClientV2("CvnVgsUc8c8672Iin3zQVtTk0l1mZtaMwtS6aGzH")
mongo_client = pymongo.MongoClient(MONGO)
db = mongo_client["findr"]


def parse_resume(resume_file, model='command'):
    # Read resume text
    resume_text = ""
    if resume_file.filename.endswith('.pdf'):
        pdf = PyPDF2.PdfReader(resume_file)
        for page in range(len(pdf.pages)):
            resume_text += pdf.pages[page].extract_text()
    else:
        resume_text = resume_file.read().decode("utf-8")
    
    # Define prompts
    name_prompt = f"Extract the person's first and last name from the following resume. Output the full name without any additional text:\n\n{resume_text}\n\nName:"
    skills_prompt = f"Extract the key skills from the following resume. Output a comma-separated list without any additional text:\n\n{resume_text}\n\nSkills:"
    experience_prompt = f"List the person's key experiences from the following resume Output a comma-separated list without any additional text:\n\n{resume_text}\n\nExperience:"
    tags_prompt = f"Generate key tags for this person based on their resume Output a comma-separated list without any additional text:\n\n{resume_text}\n\nTags:"
    summary_prompt = f"Write a single sentence background summary for the following resume:\n\n{resume_text}\n\nSummary:"
    school_prompt = f"Extract the person's University. Output the name of the school without any additional text:\n\n{resume_text}\n\nSummary:"

    # Generate responses
    responses = {
        "name": co.generate(model=model, prompt=name_prompt, max_tokens=10).generations[0].text.strip(),
        "skills": co.generate(model=model, prompt=skills_prompt, max_tokens=50).generations[0].text.strip(),
        "experience": co.generate(model=model, prompt=experience_prompt, max_tokens=100).generations[0].text.strip(),
        "tags": co.generate(model=model, prompt=tags_prompt, max_tokens=50).generations[0].text.strip(),
        "background": co.generate(model=model, prompt=summary_prompt, max_tokens=500).generations[0].text.strip(),
        "school": co.generate(model=model, prompt=school_prompt, max_tokens=50).generations[0].text.strip()
    }

    # Format as JSON
    parsed_resume = {
        "name": responses["name"],
        "skills": responses["skills"].split(", "),
        "experience": responses["experience"].split(","),
        "tags": responses["tags"].split(", "),
        "background": responses["background"],
        "school": responses["school"]
    }

    return parsed_resume


def create_user(parsed_resume):
    """Inserts a user into the database if they don't already exist."""
    users = db["users"]

    # Check if user already exists (by name and school)
    existing_user = users.find_one({
        "name": parsed_resume["name"],
        "school": parsed_resume["school"]
    })

    if existing_user:
        return {"message": "User already exists", "user_id": str(existing_user["_id"])}

    # Insert new user
    result = users.insert_one(parsed_resume)
    return {"message": "User created", "user_id": str(result.inserted_id)}

def match(user1, user2):
    """Creates a match if it does not already exist."""
    matches = db["matches"]

    # Ensure valid ObjectIds
    user1, user2 = ObjectId(user1), ObjectId(user2)

    # Check if the match already exists (in both orders)
    existing_match = matches.find_one({
        "$or": [
            {"user1": user1, "user2": user2},
            {"user1": user2, "user2": user1}
        ]
    })

    if existing_match:
        return {"message": "Match already exists"}

    # Insert match
    matches.insert_one({"user1": user1, "user2": user2})
    return {"message": "Match created"}

def get_matches(user_id):
    """Retrieves all matches for a given user."""
    matches = db["matches"]
    user_id = ObjectId(user_id)

    matches_list = matches.find({
        "$or": [{"user1": user_id}, {"user2": user_id}]
    })

    matched_user_ids = []
    for match in matches_list:
        matched_user_ids.append(str(match["user1"]) if match["user2"] == user_id else str(match["user2"]))

    return {"matches": matched_user_ids}

def remove_match(user1, user2):
    """Removes a match if it exists."""
    matches = db["matches"]

    # Ensure valid ObjectIds
    user1, user2 = ObjectId(user1), ObjectId(user2)

    # Delete match (in both orders)
    result = matches.delete_one({
        "$or": [
            {"user1": user1, "user2": user2},
            {"user1": user2, "user2": user1}
        ]
    })

    if result.deleted_count > 0:
        return {"message": "Match removed"}
    else:
        return {"message": "Match not found"}
    
def like_user(user1, user2):
    """Allows a user to like another user. If both users like each other, a match is created."""
    likes = db["likes"]

    # Convert to ObjectId
    user1, user2 = ObjectId(user1), ObjectId(user2)

    # Check if user1 has already liked user2
    existing_like = likes.find_one({"user": user1, "liked_user": user2})
    if existing_like:
        return {"message": "Already liked this user"}

    # Insert like
    likes.insert_one({"user": user1, "liked_user": user2})

    # Check if the liked user also liked the current user
    reciprocal_like = likes.find_one({"user": user2, "liked_user": user1})
    if reciprocal_like:
        match(user1, user2)
        return {"message": "Match created!"}

    return {"message": "Like added"}
