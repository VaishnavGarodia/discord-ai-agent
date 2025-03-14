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
        self.chat_history_file = os.path.join(self.data_folder, "chat_history.json")
        
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
            
        # Chat history data structure
        if not os.path.exists(self.chat_history_file):
            self._save_json(self.chat_history_file, {
                "user_histories": {}
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
    
    def submit_outfit(self, user_id, username, image_url, trend_id=None, analysis_text=None):
        """Submit a new outfit for the current trend challenge."""
        trends_data = self._load_json(self.trends_file)
        
        # Get active trend if no trend_id is provided
        if not trend_id:
            active_trend = trends_data.get("active_trend")
            if not active_trend:
                return False, "No active trend challenge found"
            trend_id = active_trend.get("name")
        
        # Create submission ID
        submission_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create submission entry
        submission = {
            "id": submission_id,
            "user_id": user_id,
            "username": username,
            "trend_id": trend_id,
            "image_url": image_url,
            "submission_date": datetime.now().isoformat(),
            "ratings": {},
            "analysis_text": analysis_text  # Store the AI analysis text
        }
        
        # Add submission
        if "submissions" not in trends_data:
            trends_data["submissions"] = {}
        trends_data["submissions"][submission_id] = submission
        
        # Add user to participants if not already there
        if active_trend and user_id not in active_trend.get("participants", []):
            trends_data["active_trend"]["participants"].append(user_id)
        
        self._save_json(self.trends_file, trends_data)
        return True, submission
    
    def rate_submission(self, user_id, trend_accuracy, creativity, fit, submission_id=None, username=None):
        """Rate a user's outfit submission."""
        trends_data = self._load_json(self.trends_file)
        
        # Find the submission to rate
        if submission_id:
            # Rate specific submission
            if submission_id not in trends_data.get("submissions", {}):
                return False, "Submission not found"
            
            submission = trends_data["submissions"][submission_id]
        else:
            # Find most recent submission for this user
            user_submissions = []
            for sid, sub in trends_data.get("submissions", {}).items():
                if str(sub.get("user_id")) == str(user_id):
                    user_submissions.append(sub)
            
            if not user_submissions:
                return False, "No submissions found for this user"
            
            # Sort by submission date and get most recent
            user_submissions.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
            submission = user_submissions[0]
            submission_id = submission["id"]
        
        # Calculate points (average of the three ratings * 10)
        average_rating = (trend_accuracy + creativity + fit) / 3
        points = int(average_rating * 10)
        
        # Update submission ratings
        trends_data["submissions"][submission_id]["ratings"] = {
            "trend_accuracy": trend_accuracy,
            "creativity": creativity,
            "fit": fit,
            "average": average_rating,
            "points": points
        }
        
        self._save_json(self.trends_file, trends_data)
        
        # Update user points
        self.add_points(user_id, points, username)
        
        return True, {
            "trend_accuracy": trend_accuracy,
            "creativity": creativity,
            "fit": fit,
            "average": average_rating,
            "points": points
        }
    
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
    
    def get_active_competition(self):
        """Get the currently active competition data."""
        comp_data = self._load_json(self.competitions_file)
        return comp_data.get("active_competition")
    
    # CHAT HISTORY MANAGEMENT
    
    def add_to_chat_history(self, user_id, message_content, ai_response, submission_id=None):
        """
        Add a message and response pair to a user's chat history.
        
        Args:
            user_id (str): Discord user ID
            message_content (str): The user's message
            ai_response (str): The AI's response
            submission_id (str, optional): ID of an outfit submission this conversation refers to
        """
        chat_data = self._load_json(self.chat_history_file)
        
        # Initialize user history if it doesn't exist
        if str(user_id) not in chat_data["user_histories"]:
            chat_data["user_histories"][str(user_id)] = []
        
        # Add the new message pair
        message_pair = {
            "timestamp": datetime.now().isoformat(),
            "user_message": message_content,
            "ai_response": ai_response,
            "submission_id": submission_id
        }
        
        # Limit chat history to the most recent 20 message pairs
        user_history = chat_data["user_histories"][str(user_id)]
        user_history.append(message_pair)
        if len(user_history) > 20:
            user_history = user_history[-20:]
        chat_data["user_histories"][str(user_id)] = user_history
        
        self._save_json(self.chat_history_file, chat_data)
    
    def get_chat_history(self, user_id, limit=5):
        """
        Get recent chat history for a user.
        
        Args:
            user_id (str): Discord user ID
            limit (int): Maximum number of message pairs to return
            
        Returns:
            list: The most recent message pairs, newest first
        """
        chat_data = self._load_json(self.chat_history_file)
        
        if str(user_id) not in chat_data["user_histories"]:
            return []
        
        user_history = chat_data["user_histories"][str(user_id)]
        return user_history[-limit:]
    
    def get_outfit_submissions_history(self, user_id, limit=3):
        """
        Get user's recent outfit submissions for context in feedback.
        
        Args:
            user_id (str): Discord user ID
            limit (int): Maximum number of submissions to return
            
        Returns:
            list: The most recent submissions with AI feedback
        """
        trends_data = self._load_json(self.trends_file)
        
        user_submissions = []
        for submission_id, submission in trends_data.get("submissions", {}).items():
            if str(submission.get("user_id")) == str(user_id):
                user_submissions.append(submission)
        
        # Sort by submission date, newest first
        user_submissions.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
        
        return user_submissions[:limit]