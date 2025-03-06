import os
from mistralai import Mistral
import discord
import random
import json
from data_manager import DataManager

MISTRAL_MODEL = "mistral-large-latest"
SYSTEM_PROMPT = """You are FashionBot, a fashion-forward AI assistant with expertise in style trends and fashion critique.
You're designed to help users with fashion challenges, rate outfits based on trends, and provide friendly, constructive feedback.
Be knowledgeable but approachable, and express enthusiasm about fashion while giving honest assessments."""

RATING_PROMPT = """Analyze this outfit submission for the {trend_name} trend challenge: {image_url}

Provide ratings (1-10) for:
1. Trend Accuracy: How well the outfit aligns with the {trend_name} aesthetic
2. Creativity: Unique interpretation and styling choices
3. Overall Fit: How well the pieces work together and flatter the wearer

For each rating, provide specific feedback. Be constructive, positive, but honest. 
Format your response with clear headers and ratings, followed by a brief summary paragraph.

Trend Description: {trend_description}"""

class MistralAgent:
    def __init__(self):
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        self.client = Mistral(api_key=MISTRAL_API_KEY)
        self.data_manager = DataManager()
        
        # Sample trend ideas for inspiration
        self.trend_ideas = [
            "Y2K Revival", "Quiet Luxury", "Barbiecore", "Dark Academia", 
            "Coastal Grandmother", "Cottagecore", "Cyberpunk", "Gorpcore",
            "Balletcore", "Regencycore", "Indie Sleaze", "Streetwear", 
            "Punk Revival", "Western Chic", "Normcore", "Dopamine Dressing"
        ]
        
        # Descriptions for trends
        self.trend_descriptions = {
            "Y2K Revival": "Late 90s/early 2000s nostalgia with low-rise jeans, baby tees, butterflies, and playful accessories.",
            "Quiet Luxury": "Understated elegance with high-quality basics, neutral colors, and minimal branding.",
            "Barbiecore": "Playful pink aesthetics inspired by Barbie, featuring bold pink hues, plastic accessories, and feminine silhouettes.",
            "Dark Academia": "Scholarly aesthetic with vintage-inspired pieces like tweed, plaid, oxford shirts, and leather accessories.",
            "Coastal Grandmother": "Breezy, elegant coastal style with linen, neutral tones, straw hats, and comfortable yet refined pieces.",
            "Cottagecore": "Romanticized rural aesthetic with floral prints, prairie dresses, natural fabrics, and vintage-inspired pieces.",
            "Cyberpunk": "Futuristic aesthetic with metallic fabrics, neon accents, tech accessories, and edgy silhouettes.",
            "Gorpcore": "Outdoorsy, functional fashion featuring technical gear, fleece, hiking boots, and practical accessories.",
            "Balletcore": "Ballet-inspired fashion with leg warmers, wrap tops, tulle skirts, bodysuits, and soft, flowing fabrics.",
            "Regencycore": "Regency era-inspired fashion with empire waistlines, lace details, puff sleeves, and romantic elements.",
            "Indie Sleaze": "Gritty, flash-photography aesthetic with layered vintage pieces, band tees, and a deliberately disheveled look.",
            "Streetwear": "Urban casual style with graphic tees, hoodies, sneakers, and statement accessories.",
            "Punk Revival": "Edgy style with leather, studs, plaid, combat boots, and DIY elements.",
            "Western Chic": "Modern cowboy aesthetic with denim, fringe, boots, and Western-inspired accessories.",
            "Normcore": "Intentionally ordinary, unremarkable clothing focusing on basics and practical pieces.",
            "Dopamine Dressing": "Joy-inducing fashion with bold colors, fun patterns, and playful accessories to boost mood."
        }

    async def run(self, message: discord.Message):
        # Check if this is a command that should be processed elsewhere
        if message.content.startswith("!"):
            return await self.process_command(message)
            
        # Default response - general fashion advice
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message.content},
        ]

        response = await self.client.chat.complete_async(
            model=MISTRAL_MODEL,
            messages=messages,
        )

        return response.choices[0].message.content
    
    async def process_command(self, message: discord.Message):
        # Split the command into parts
        parts = message.content.split()
        command = parts[0].lower()
        
        # Process the different commands
        if command == "!trend":
            return await self.handle_trend_command(message, parts)
        elif command == "!submit":
            return await self.handle_submit_command(message)
        elif command == "!leaderboard":
            return await self.handle_leaderboard_command(message)
        elif command == "!points":
            return await self.handle_points_command(message)
        elif command == "!competition":
            return await self.handle_competition_command(message, parts)
        elif command == "!vote":
            return await self.handle_vote_command(message, parts)
        elif command == "!help":
            return await self.handle_help_command(message)
        
        # If it's not one of our commands, return None so the main bot can handle it
        return None
        
    async def handle_trend_command(self, message: discord.Message, parts):
        if len(parts) < 2:
            return """
**Trend Command Help**
- `!trend announce [name]` - Announce a new trend challenge
- `!trend end` - End the current trend challenge
- `!trend list` - List available trend ideas
- `!trend status` - Show current active trend
"""
        
        action = parts[1].lower()
        
        if action == "announce":
            # If trend name is provided, use it. Otherwise, pick a random one
            if len(parts) >= 3:
                trend_name = " ".join(parts[2:])
                # If we don't have a description, ask Mistral to generate one
                description_prompt = f"Create a brief description (2-3 sentences) of the fashion trend '{trend_name}'. Include key style elements, signature pieces, and overall aesthetic."
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": description_prompt},
                ]
                response = await self.client.chat.complete_async(
                    model=MISTRAL_MODEL,
                    messages=messages,
                )
                description = response.choices[0].message.content
            else:
                return "Please provide a trend name: `!trend announce [trend name]`"
            
            success, result = self.data_manager.announce_trend(trend_name, description)
            
            if success:
                return f"""
## 🌟 New Trend Challenge Announced! 🌟

**{trend_name}**

{description}

**How to participate:**
1. Style an outfit matching this trend
2. Take a photo of your outfit
3. Submit with `!submit` and attach your image
4. Get AI feedback and earn points!

Challenge ends in {result['duration_days']} days. Good luck, fashionistas!
"""
            else:
                return f"Could not announce trend: {result}"
                
        elif action == "end":
            success, result = self.data_manager.end_current_trend()
            if success:
                return "The current trend challenge has ended. Check the leaderboard to see the results!"
            else:
                return f"Error: {result}"
                
        elif action == "list":
            trend_list = "\n".join([f"- {trend}" for trend in self.trend_ideas])
            return f"""
**Available Trend Ideas:**
{trend_list}

Use `!trend announce [trend name]` to start a challenge with one of these trends.
"""
        
        elif action == "status":
            active_trend = self.data_manager.get_active_trend()
            if active_trend:
                return f"""
**Current Trend Challenge: {active_trend['name']}**

{active_trend['description']}

Participants: {len(active_trend['participants'])}
Started: {active_trend['start_date']}
"""
            else:
                return "No active trend challenge at the moment."
        
        return "Unknown trend command. Try `!trend` for help."
    
    async def handle_submit_command(self, message: discord.Message):
        # Check if there's an active trend
        active_trend = self.data_manager.get_active_trend()
        if not active_trend:
            return "Sorry, there's no active trend challenge to submit to. Wait for the next announcement!"
        
        # Check if there's an image attachment
        if not message.attachments:
            return "Please attach an image of your outfit to submit for the trend challenge."
        
        image_url = message.attachments[0].url
        
        # Save the submission
        success, submission = self.data_manager.submit_outfit(
            message.author.id, 
            message.author.name,
            image_url
        )
        
        if not success:
            return f"Error submitting your outfit: {submission}"
        
        # Enhanced rating prompt with detailed image analysis instructions
        rating_message = f"""Analyze this outfit submission for the {active_trend['name']} trend challenge. 
The image URL is: {image_url}

IMPORTANT INSTRUCTIONS:
1. First, describe what you see in the image in detail (clothing items, colors, accessories, styling)
2. Then analyze how these visual elements relate to the {active_trend['name']} trend
3. MUST provide numerical ratings on a scale of 1-10 for each category

Please rate this outfit on the following criteria:
1. Trend Accuracy (1-10): How well does this outfit align with the {active_trend['name']} aesthetic? Reference specific visual elements.
2. Creativity (1-10): How unique and innovative is the styling? Point out specific creative choices.
3. Overall Fit (1-10): How well do the pieces work together as a cohesive look? Discuss proportions and styling.

For each rating, provide specific feedback about what works well and what could be improved.
Format your response with clear headers and explicit numerical ratings (e.g., "Trend Accuracy: 8/10").

Trend Description: {active_trend['description']}

Your analysis MUST be based on the actual visual elements in the image. Be specific about what you see.
Remember to be constructive, specific, and fair in your assessment.
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": rating_message},
        ]
        
        # Add retry logic for more reliability
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.complete_async(
                    model=MISTRAL_MODEL,
                    messages=messages,
                    temperature=0.3,  # Lower temperature for more accurate analysis
                    max_tokens=1500,  # Ensure we get a complete response with detailed analysis
                )
                
                ai_feedback = response.choices[0].message.content
                
                # Improved rating extraction
                trend_accuracy, creativity, fit = self.extract_ratings(ai_feedback)
                
                # Validate ratings are in proper range
                if not (1 <= trend_accuracy <= 10 and 1 <= creativity <= 10 and 1 <= fit <= 10):
                    if attempt < max_retries - 1:
                        continue  # Try again if ratings are invalid
                    else:
                        # Use default values if we've exhausted retries
                        trend_accuracy = max(1, min(trend_accuracy, 10))
                        creativity = max(1, min(creativity, 10))
                        fit = max(1, min(fit, 10))
                
                # Save ratings
                self.data_manager.rate_submission(
                    message.author.id,
                    trend_accuracy,
                    creativity,
                    fit,
                    username=message.author.name
                )
                
                # Get updated user info
                user_info = self.data_manager.get_user(message.author.id)
                
                return f"""
## Outfit Submission for {active_trend['name']}

{ai_feedback}

**Points earned:** {int((trend_accuracy + creativity + fit) / 3 * 10)}
**Total points:** {user_info['points']}

Thank you for participating! Check the leaderboard with `!leaderboard`
"""
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error during image analysis (attempt {attempt+1}): {e}")
                    continue
                else:
                    return "Sorry, I encountered an error analyzing your outfit. Please try again later."
    
    def extract_ratings(self, feedback):
        try:
            # Default values
            trend_accuracy = creativity = fit = 7.0
            
            # More robust pattern matching
            import re
            
            # Look for ratings in format like "Trend Accuracy: 8/10" or "Trend Accuracy: 8"
            trend_match = re.search(r'trend accuracy:?\s*(\d+(?:\.\d+)?)[/\s]*(?:10)?', feedback.lower())
            if trend_match:
                trend_accuracy = float(trend_match.group(1))
            
            creativity_match = re.search(r'creativity:?\s*(\d+(?:\.\d+)?)[/\s]*(?:10)?', feedback.lower())
            if creativity_match:
                creativity = float(creativity_match.group(1))
            
            fit_match = re.search(r'(?:overall\s+)?fit:?\s*(\d+(?:\.\d+)?)[/\s]*(?:10)?', feedback.lower())
            if fit_match:
                fit = float(fit_match.group(1))
            
            # Ensure ratings are within valid range
            trend_accuracy = max(1.0, min(trend_accuracy, 10.0))
            creativity = max(1.0, min(creativity, 10.0))
            fit = max(1.0, min(fit, 10.0))
            
            return trend_accuracy, creativity, fit
            
        except Exception as e:
            print(f"Error extracting ratings: {e}")
            return 7.0, 7.0, 7.0
    
    async def handle_leaderboard_command(self, message: discord.Message):
        leaderboard = self.data_manager.get_leaderboard(10)
        
        if not leaderboard:
            return "No participants in the leaderboard yet."
        
        leaderboard_text = "\n".join([
            f"{i+1}. **{entry[1]['username']}** - {entry[1]['points']} points (Wins: {entry[1]['wins']})"
            for i, entry in enumerate(leaderboard)
        ])
        
        return f"""
## 👑 Fashion Trend Challenge Leaderboard 👑

{leaderboard_text}

Earn points by submitting outfits to trend challenges and winning competitions!
"""
    
    async def handle_points_command(self, message: discord.Message):
        user_info = self.data_manager.get_user(message.author.id)
        
        if not user_info:
            return "You haven't participated in any challenges yet. Submit an outfit to get started!"
        
        return f"""
## Style Stats for {message.author.name}

**Points:** {user_info['points']}
**Participations:** {user_info['participations']}
**Competition Wins:** {user_info['wins']}

Keep styling to earn more points and unlock rewards!
"""
    
    async def handle_competition_command(self, message: discord.Message, parts):
        # Check if user has admin permissions for certain actions
        if len(parts) < 2:
            return """
**Competition Command Help**
- `!competition start [name]` - Start a new styling competition
- `!competition end` - End the current competition
- `!competition status` - Show current active competition
- `!competition submit` - Submit an entry (with image attachment)
"""
        
        action = parts[1].lower()
        
        if action == "start":
            if len(parts) < 3:
                return "Please provide a name for the competition."
                
            competition_name = " ".join(parts[2:])
            
            # Generate description using Mistral
            description_prompt = f"Create a description for a fashion styling competition called '{competition_name}'. Include what contestants should focus on and criteria for winning. Keep it under 100 words."
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": description_prompt},
            ]
            response = await self.client.chat.complete_async(
                model=MISTRAL_MODEL,
                messages=messages,
            )
            description = response.choices[0].message.content
            
            # Generate sponsor
            sponsors = ["StyleCo", "Fashion Forward", "Trend Setters", "ChicBoutique", "Urban Edge"]
            sponsor = random.choice(sponsors)
            
            success, result = self.data_manager.start_competition(
                competition_name, 
                description, 
                sponsor
            )
            
            if success:
                return f"""
## 🏆 New Styling Competition: {competition_name} 🏆

{description}

**Sponsored by:** {sponsor}

**How to participate:**
1. Style your best outfit for this theme
2. Take a photo
3. Submit with `!competition submit` and attach your image
4. Other users can vote for their favorites with `!vote [username]`

Competition runs for {result['duration_days']} days. The winner gets 100 bonus points!
"""
            else:
                return f"Could not start competition: {result}"
                
        elif action == "end":
            success, result = self.data_manager.end_competition()
            
            if success:
                winner_text = ""
                if "winner" in result:
                    winner_text = f"🎉 **WINNER: {result['winner']['username']}** with {result['winner']['votes']} votes! 🎉"
                
                return f"""
## Competition Ended: {result['name']}

{winner_text}

Thank you to all {len(result['participants'])} participants!
The winner has been awarded 100 bonus points.

Stay tuned for the next competition!
"""
            else:
                return f"Error: {result}"
                
        elif action == "status":
            comp_data = self._load_json(self.competitions_file)
            active_comp = comp_data.get("active_competition")
            
            if not active_comp:
                return "No active competition at the moment."
                
            participant_count = len(active_comp['participants'])
                
            return f"""
## Active Competition: {active_comp['name']}

{active_comp['description']}

**Sponsored by:** {active_comp['sponsor']}
**Participants:** {participant_count}
**Started:** {active_comp['start_date']}

Submit your entry with `!competition submit` and attach a photo!
"""
        
        elif action == "submit":
            # Check for image attachment
            if not message.attachments:
                return "Please attach an image of your outfit to submit for the competition."
                
            image_url = message.attachments[0].url
            
            # Check for description in the message
            description = ""
            if len(parts) > 2:
                description = " ".join(parts[2:])
            else:
                description = "No description provided."
                
            success, result = self.data_manager.submit_competition_entry(
                message.author.id,
                message.author.name,
                image_url,
                description
            )
            
            if success:
                return f"""
## Competition Entry Submitted!

Your entry for the current competition has been recorded.

Other users can vote for your entry using:
`!vote {message.author.name}`

Good luck!
"""
            else:
                return f"Error submitting your entry: {result}"
        
        return "Unknown competition command. Try `!competition` for help."
    
    async def handle_vote_command(self, message: discord.Message, parts):
        if len(parts) < 2:
            return "Please specify a username to vote for: `!vote [username]`"
            
        username = parts[1]
        
        target_user = None
        for member in message.guild.members:
            if member.name.lower() == username.lower():
                target_user = member
                break
                
        if not target_user:
            return f"Could not find user '{username}'. Please check the spelling."
            
        success, result = self.data_manager.vote_for_submission(
            message.author.id,
            target_user.id
        )
        
        if success:
            return f"You have successfully voted for {username}'s competition entry!"
        else:
            return f"Error: {result}"
    
    async def handle_help_command(self, message: discord.Message):
        return """
## 👗 FashionBot Commands 👗

**Trend Challenges:**
- `!trend announce [name]` - Start a new trend challenge
- `!trend end` - End the current trend challenge
- `!trend list` - See available trend ideas
- `!trend status` - Show the current active trend

**Participation:**
- `!submit` - Submit your outfit for the current trend (attach photo)
- `!points` - Check your points and stats
- `!leaderboard` - View the top fashionistas

**Competitions:**
- `!competition start [name]` - Start a styling competition
- `!competition end` - End the current competition
- `!competition status` - Show current competition info
- `!competition submit` - Submit your entry (attach photo)
- `!vote [username]` - Vote for someone's competition entry

For any fashion advice, just message me directly!
"""
