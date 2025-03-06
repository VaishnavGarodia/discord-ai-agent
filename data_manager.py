import json
import os
from datetime import datetime
import random

class DataManager:
    def __init__(self):
        self.data_folder = "data"
        self.trends_file = os.path.join(self.data_folder, "trends.json")
        self.users_file = os.path.join(self.data_folder, "users.json")
        self.competitions_file = os.path.join(self.data_folder, "competitions.json")
        
        # Create data folder if it doesn't exist
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        # Initialize data files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        # Trends data structure
        if not os.path.exists(self.trends_file):
            self._save_json(self.trends_file, {
                "active_trend": None,
                "past_trends": [],
                "submissions": {}
            })
        
        # Users data structure
        if not os.path.exists(self.users_file):
            self._save_json(self.users_file, {
                "users": {}
            })
            
        # Competitions data structure
        if not os.path.exists(self.competitions_file):
            self._save_json(self.competitions_file, {
                "active_competition": None,
                "past_competitions": [],
                "votes": {}
            })
    
    def _load_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_json(self, file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    # TREND MANAGEMENT
    
    def announce_trend(self, trend_name, description, duration_days=7):
        trends_data = self._load_json(self.trends_file)
        
        # Check if there's already an active trend
        if trends_data.get("active_trend"):
            return False, "There's already an active trend challenge"
        
        # Create new trend
        new_trend = {
            "name": trend_name,
            "description": description,
            "start_date": datetime.now().isoformat(),
            "end_date": datetime.now().isoformat(),  # Will be calculated based on duration
            "duration_days": duration_days,
            "participants": []
        }
        
        trends_data["active_trend"] = new_trend
        trends_data["submissions"] = {}
        
        self._save_json(self.trends_file, trends_data)
        return True, new_trend
    
    def get_active_trend(self):
        trends_data = self._load_json(self.trends_file)
        return trends_data.get("active_trend")
    
    def end_current_trend(self):
        trends_data = self._load_json(self.trends_file)
        
        if not trends_data.get("active_trend"):
            return False, "No active trend to end"
        
        # Move active trend to past trends
        trends_data["past_trends"].append(trends_data["active_trend"])
        trends_data["active_trend"] = None
        
        self._save_json(self.trends_file, trends_data)
        return True, "Trend challenge ended successfully"
    
    def submit_outfit(self, user_id, username, image_url, trend_id=None):
        trends_data = self._load_json(self.trends_file)
        
        if not trends_data.get("active_trend"):
            return False, "No active trend challenge to submit to"
        
        # Add submission
        if str(user_id) not in trends_data["submissions"]:
            trends_data["submissions"][str(user_id)] = []
        
        submission = {
            "user_id": str(user_id),
            "username": username,
            "image_url": image_url,
            "timestamp": datetime.now().isoformat(),
            "rating": None
        }
        
        trends_data["submissions"][str(user_id)].append(submission)
        
        if user_id not in trends_data["active_trend"]["participants"]:
            trends_data["active_trend"]["participants"].append(user_id)
        
        self._save_json(self.trends_file, trends_data)
        return True, submission
    
    def rate_submission(self, user_id, trend_accuracy, creativity, fit, username=None):
        trends_data = self._load_json(self.trends_file)
        
        if not trends_data.get("active_trend"):
            return False, "No active trend challenge"
        
        if str(user_id) not in trends_data["submissions"]:
            return False, "No submission found for this user"
        
        # Rate the latest submission
        latest_submission = trends_data["submissions"][str(user_id)][-1]
        
        # Get the username from the submission
        submission_username = latest_submission["username"]
        
        rating = {
            "trend_accuracy": trend_accuracy,
            "creativity": creativity,
            "fit": fit,
            "total": (trend_accuracy + creativity + fit) / 3
        }
        
        latest_submission["rating"] = rating
        
        # Update submission in data
        trends_data["submissions"][str(user_id)][-1] = latest_submission
        
        # Add points to user, passing the proper username
        self.add_points(user_id, int(rating["total"] * 10), username=submission_username)
        
        self._save_json(self.trends_file, trends_data)
        return True, rating
    
    # USER/POINTS MANAGEMENT
    
    def get_user(self, user_id):
        users_data = self._load_json(self.users_file)
        return users_data["users"].get(str(user_id))
    
    def add_points(self, user_id, points, username=None):
        users_data = self._load_json(self.users_file)
        
        if str(user_id) not in users_data["users"]:
            users_data["users"][str(user_id)] = {
                "username": username or f"User{user_id}",
                "points": 0,
                "participations": 0,
                "wins": 0
            }
        
        users_data["users"][str(user_id)]["points"] += points
        users_data["users"][str(user_id)]["participations"] += 1
        
        self._save_json(self.users_file, users_data)
        return users_data["users"][str(user_id)]
    
    def get_leaderboard(self, limit=10):
        users_data = self._load_json(self.users_file)
        
        # Sort users by points
        sorted_users = sorted(
            users_data["users"].items(),
            key=lambda x: x[1]["points"],
            reverse=True
        )
        
        return sorted_users[:limit]
    
    def update_usernames_in_database(self, guild):
        """
        Update all username entries in the database with actual Discord usernames.
        Should be called once during bot initialization.
        """
        users_data = self._load_json(self.users_file)
        
        for user_id in list(users_data["users"].keys()):
            # Try to find the member in the guild
            member = guild.get_member(int(user_id))
            if member:
                # Update the username
                users_data["users"][user_id]["username"] = member.name
        
        self._save_json(self.users_file, users_data)
        return True
    
    # COMPETITION MANAGEMENT
    
    def start_competition(self, name, description, sponsor, duration_days=7):
        comp_data = self._load_json(self.competitions_file)
        
        if comp_data.get("active_competition"):
            return False, "There's already an active competition"
        
        # Create new competition
        new_competition = {
            "name": name,
            "description": description,
            "sponsor": sponsor,
            "start_date": datetime.now().isoformat(),
            "end_date": datetime.now().isoformat(),  # Will be calculated based on duration
            "duration_days": duration_days,
            "participants": [],
            "submissions": {}
        }
        
        comp_data["active_competition"] = new_competition
        comp_data["votes"] = {}
        
        self._save_json(self.competitions_file, comp_data)
        return True, new_competition
    
    def submit_competition_entry(self, user_id, username, image_url, description):
        comp_data = self._load_json(self.competitions_file)
        
        if not comp_data.get("active_competition"):
            return False, "No active competition to submit to"
        
        # Add submission
        if str(user_id) not in comp_data["active_competition"]["submissions"]:
            comp_data["active_competition"]["submissions"][str(user_id)] = []
        
        submission = {
            "user_id": str(user_id),
            "username": username,
            "image_url": image_url,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "votes": 0
        }
        
        comp_data["active_competition"]["submissions"][str(user_id)].append(submission)
        
        if user_id not in comp_data["active_competition"]["participants"]:
            comp_data["active_competition"]["participants"].append(user_id)
        
        self._save_json(self.competitions_file, comp_data)
        return True, submission
    
    def vote_for_submission(self, voter_id, user_id):
        comp_data = self._load_json(self.competitions_file)
        
        if not comp_data.get("active_competition"):
            return False, "No active competition"
        
        if str(user_id) not in comp_data["active_competition"]["submissions"]:
            return False, "No submission found for this user"
        
        # Check if voter has already voted
        if str(voter_id) in comp_data["votes"]:
            return False, "You have already voted in this competition"
        
        # Record vote
        comp_data["votes"][str(voter_id)] = str(user_id)
        
        # Increment vote count for submission
        latest_submission = comp_data["active_competition"]["submissions"][str(user_id)][-1]
        latest_submission["votes"] += 1
        
        # Update submission
        comp_data["active_competition"]["submissions"][str(user_id)][-1] = latest_submission
        
        # Add points to user
        self.add_points(user_id, 10)
        
        self._save_json(self.competitions_file, comp_data)
        return True, "Vote recorded successfully"
    
    def end_competition(self):
        comp_data = self._load_json(self.competitions_file)
        users_data = self._load_json(self.users_file)
        
        if not comp_data.get("active_competition"):
            return False, "No active competition to end"
        
        # Determine winner (submission with most votes)
        winner_id = None
        max_votes = -1
        
        for user_id, submissions in comp_data["active_competition"]["submissions"].items():
            if submissions[-1]["votes"] > max_votes:
                max_votes = submissions[-1]["votes"]
                winner_id = user_id
        
        # Add winner information to competition
        if winner_id:
            comp_data["active_competition"]["winner"] = {
                "user_id": winner_id,
                "username": comp_data["active_competition"]["submissions"][winner_id][-1]["username"],
                "votes": max_votes
            }
            
            # Update winner's stats
            if str(winner_id) in users_data["users"]:
                users_data["users"][str(winner_id)]["wins"] += 1
                users_data["users"][str(winner_id)]["points"] += 100  # Bonus points for winning
        
        # Move to past competitions
        comp_data["past_competitions"].append(comp_data["active_competition"])
        comp_data["active_competition"] = None
        comp_data["votes"] = {}
        
        self._save_json(self.competitions_file, comp_data)
        self._save_json(self.users_file, users_data)
        
        return True, comp_data["past_competitions"][-1]