import os
from dotenv import load_dotenv
import discord
import random
import json
from data_manager import DataManager
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import re
import base64


# Load environment variables
load_dotenv()

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

print(f"Initializing Gemini with API key: {GEMINI_API_KEY[:5]}...")  # Debug log
genai.configure(api_key=GEMINI_API_KEY)

class MistralAgent:
    def __init__(self):
        self.data_manager = DataManager()
        try:
            # Initialize Gemini model with the correct model name
            self.vision_model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')  # For text interactions
            print("Gemini models initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini models: {str(e)}")
            raise
        
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

    def clear_chat_history(self):
        """Clear any stored chat history to ensure fresh analysis."""
        if hasattr(self, 'chat_history'):
            self.chat_history = []

    async def run(self, message: discord.Message):
        # Check if this is a command that should be processed elsewhere
        if message.content.startswith("!"):
            return await self.process_command(message)
            
        # Get user's recent chat history for context
        user_history = self.data_manager.get_chat_history(message.author.id, limit=3)
        
        # Prepare context from chat history
        context = ""
        if user_history:
            context = "Previous conversation:\n"
            for entry in user_history:
                context += f"User: {entry['user_message']}\nAI: {entry['ai_response'][:100]}...\n\n"
        
        # Get recent submissions for context
        recent_submissions = self.data_manager.get_outfit_submissions_history(message.author.id, limit=1)
        if recent_submissions:
            recent = recent_submissions[0]
            context += f"\nUser's most recent outfit submission had ratings:\n"
            context += f"Trend Accuracy: {recent.get('ratings', {}).get('trend_accuracy', 'N/A')}/10\n"
            context += f"Creativity: {recent.get('ratings', {}).get('creativity', 'N/A')}/10\n"
            context += f"Overall Fit: {recent.get('ratings', {}).get('fit', 'N/A')}/10\n"
        
        # Generate response using the text model  
        prompt = f"""You are a helpful and friendly fashion assistant bot that provides fashion advice.
        
{context}

Current user question: {message.content}

Respond in a friendly, conversational way. If they're asking about fashion, provide specific, actionable advice.
If they have previous outfit submissions, refer to them when relevant. If they're asking about something
unrelated to fashion, you can answer briefly but encourage fashion-related questions.

Remember they can submit outfits with !submit and get feedback on their last outfit with !feedback [question].
"""

        try:
            response = self.text_model.generate_content(prompt)
            ai_response = response.text
            
            # Save to chat history
            self.data_manager.add_to_chat_history(
                message.author.id,
                message.content,
                ai_response
            )
            
            return self.split_message(ai_response)
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "Sorry, I couldn't process your request right now. Please try again later."
    
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
        elif command == "!feedback":
            return await self.handle_feedback_command(message)
        else:
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
                # If we don't have a description, ask gemini to generate one
                description_prompt = f"Create a brief description (2-3 sentences) of the fashion trend '{trend_name}'. Include key style elements, signature pieces, and overall aesthetic."
                
                # Generate description using the text model
                response = self.text_model.generate_content(description_prompt)
                description = response.text
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
        """Handle outfit submissions using Gemini Vision."""
        try:
            # Check if there's an active trend
            active_trend = self.data_manager.get_active_trend()
            if not active_trend:
                return "Sorry, there's no active trend challenge to submit to. Wait for the next announcement!"
            
            # Check for image attachment
            if not message.attachments:
                return "Please attach an image of your outfit to submit for the trend challenge."
            
            image_url = message.attachments[0].url
            print(f"Processing image from URL: {image_url}")  # Debug log
            
            try:
                # Download and process the image
                response = requests.get(image_url)
                print(f"Image download status: {response.status_code}")  # Debug log
                
                if response.status_code != 200:
                    return "Error downloading the image. Please try again."
                
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                
                # Convert image to RGB if it's not
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if image is too large
                max_size = (1024, 1024)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                print(f"Image processed successfully. Mode: {img.mode}, Size: {img.size}")  # Debug log
                
                # Create the prompt for Gemini
                prompt = f"""Analyze this outfit for the {active_trend['name']} trend challenge.

REQUIREMENTS:
1. Be extremely specific about colors and items you can see
2. Only describe what is clearly visible
3. Rate on three criteria (1-10 scale)

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

## Visual Inventory
- Top: [exact description]
- Bottom: [exact description]
- Footwear: [if visible]
- Accessories: [only visible items]
- Colors: [exact colors seen]

## Style Analysis
[How the outfit relates to the {active_trend['name']} trend]

## Ratings
Trend Accuracy: [X]/10
[Specific justification]

Creativity: [X]/10
[Specific justification]

Overall Fit: [X]/10
[Specific justification]

## Summary
[Brief assessment]

## Improvement Tips
[2-3 specific suggestions to improve this outfit]"""

                print("Sending request to Gemini...")  # Debug log
                
                # Convert image to base64 for Gemini
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                img_b64 = base64.b64encode(img_byte_arr).decode('utf-8')
                
                # Get Gemini's analysis
                try:
                    response = self.vision_model.generate_content([
                        prompt,
                        {
                            "mime_type": "image/jpeg",
                            "data": img_b64
                        }
                    ])
                    print(f"Gemini response received: {response}")  # Debug log
                    
                except Exception as e:
                    print(f"Gemini API error: {str(e)}")
                    if "deprecated" in str(e).lower():
                        print(f"Full error: {str(e)}")  # Additional debug logging
                        return "Sorry, there was an error with the image analysis service. Please contact the bot administrator."
                    return "Error analyzing the image. Please try again."
                
                if not response.text:
                    return "Sorry, I couldn't analyze the image. Please try again."
                    
                analysis = response.text
                print(f"Analysis text: {analysis[:100]}...")  # Debug log
                
                # Extract ratings using regex
                trend_match = re.search(r'Trend Accuracy:\s*(\d+)', analysis)
                creativity_match = re.search(r'Creativity:\s*(\d+)', analysis)
                fit_match = re.search(r'Overall Fit:\s*(\d+)', analysis)
                
                trend_accuracy = float(trend_match.group(1)) if trend_match else 5.0
                creativity = float(creativity_match.group(1)) if creativity_match else 5.0
                fit = float(fit_match.group(1)) if fit_match else 5.0
                
                # Save submission and ratings with analysis text
                success, submission = self.data_manager.submit_outfit(
                    message.author.id,
                    message.author.name,
                    image_url,
                    analysis_text=analysis
                )
                
                if not success:
                    return f"Error submitting your outfit: {submission}"
                
                # Save the ratings
                self.data_manager.rate_submission(
                    message.author.id,
                    trend_accuracy,
                    creativity,
                    fit,
                    submission_id=submission["id"],
                    username=message.author.name
                )
                
                # Get updated user info
                user_info = self.data_manager.get_user(message.author.id)
                
                # Format response
                response_text = f"""
## Outfit Submission for {active_trend['name']}

{analysis}

**Points earned:** {int((trend_accuracy + creativity + fit) / 3 * 10)}
**Total points:** {user_info['points']}

Thank you for participating! Check the leaderboard with `!leaderboard`
Need more feedback? Ask me with `!feedback YOUR QUESTION`
"""
                
                # Save message in chat history
                self.data_manager.add_to_chat_history(
                    message.author.id,
                    f"!submit [image]",
                    response_text,
                    submission_id=submission["id"]
                )
                
                return self.split_message(response_text)
                
            except requests.RequestException as e:
                print(f"Error downloading image: {str(e)}")
                return "Error downloading the image. Please try again."
            except Image.UnidentifiedImageError:
                print("Error: Could not identify image format")
                return "Error: The image format is not supported. Please try a different image."
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                import traceback
                traceback.print_exc()
                return "Error processing the image. Please try again."
            
        except Exception as e:
            print(f"General error in handle_submit_command: {str(e)}")
            import traceback
            traceback.print_exc()
            return "Sorry, there was an error analyzing your image. Please try again."
    
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
            
            # Generate description using the text model
            description_prompt = f"Create a description for a fashion styling competition called '{competition_name}'. Include what contestants should focus on and criteria for winning. Keep it under 100 words."
            response = self.text_model.generate_content(description_prompt)
            description = response.text
            
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
            active_comp = self.data_manager.get_active_competition()
            
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
        """Generate and display help information."""
        help_text = """
## FashionBot Commands

### Outfit Analysis
- **!submit** - Submit an outfit image for the current trend challenge
- **!feedback [question]** - Ask for more detailed feedback or advice about your last outfit submission

### Trends
- **!trend** - View current trend challenge info
- **!trend new [name] [description]** - (Admin) Start a new trend challenge
- **!trend end** - (Admin) End the current trend challenge

### Competitions
- **!competition** - View active competition
- **!competition new [name] [description] [sponsor]** - (Admin) Start a new competition
- **!competition end** - (Admin) End the competition and calculate winners
- **!vote [@user]** - Vote for someone's competition entry

### Personal Stats
- **!points** - Check your current points
- **!leaderboard** - View the top users and their points

### General
- **!help** - Show this help message

For any fashion advice, just message me directly!
"""
        return help_text

    async def handle_feedback_command(self, message: discord.Message):
        """
        Handle feedback requests about outfit submissions.
        This allows users to ask follow-up questions about their outfits.
        """
        try:
            # Get user's chat history
            user_history = self.data_manager.get_chat_history(message.author.id)
            
            # Get user's recent submissions
            recent_submissions = self.data_manager.get_outfit_submissions_history(message.author.id)
            
            if not recent_submissions:
                response = "You don't have any recent outfit submissions. Submit an outfit first with `!submit`."
                self.data_manager.add_to_chat_history(message.author.id, message.content, response)
                return response
            
            # Get user's query from the message
            user_query = message.content.replace("!feedback", "", 1).strip()
            if not user_query:
                response = "Please include a question about your outfit. For example: `!feedback How can I improve my color coordination?`"
                self.data_manager.add_to_chat_history(message.author.id, message.content, response)
                return response
            
            # Get most recent submission with analysis
            most_recent = recent_submissions[0]
            
            # Create a prompt for the AI
            prompt = f"""You are a fashion advisor analyzing a user's outfit. They submitted an outfit and received feedback, and now they're asking for more information.

Here is the original analysis of their outfit:
{most_recent.get('analysis_text', 'No analysis available')}

The ratings were:
Trend Accuracy: {most_recent.get('ratings', {}).get('trend_accuracy', 'N/A')}/10
Creativity: {most_recent.get('ratings', {}).get('creativity', 'N/A')}/10
Overall Fit: {most_recent.get('ratings', {}).get('fit', 'N/A')}/10

The user is asking: "{user_query}"

Give them specific, constructive advice based on the original analysis. Be encouraging while providing practical tips they can use.
Focus on:
1. Direct answers to their questions
2. Specific, actionable improvement suggestions
3. Encouragement and positive reinforcement
4. Trend-relevant advice

Format your response in clear, helpful paragraphs with bullet points for specific tips.
"""
            try:
                response = self.text_model.generate_content(prompt)
                ai_response = response.text
                
                # Save to chat history
                self.data_manager.add_to_chat_history(
                    message.author.id,
                    message.content,
                    ai_response,
                    submission_id=most_recent.get('id')
                )
                
                return self.split_message(ai_response)
                
            except Exception as e:
                print(f"Error generating feedback: {str(e)}")
                return "Sorry, I couldn't generate feedback at the moment. Please try again later."
                
        except Exception as e:
            print(f"Error in handle_feedback_command: {str(e)}")
            import traceback
            traceback.print_exc()
            return "Sorry, there was an error processing your feedback request. Please try again."

    def split_message(self, message, limit=1900):
        """Split a message into chunks that fit within Discord's character limit."""
        if not message:
            return ["No response generated."]
        
        if len(message) <= limit:
            return [message]
        
        chunks = []
        lines = message.split('\n')
        current_chunk = ""

        for line in lines:
            # If this line would make the chunk too long, start a new chunk
            if len(current_chunk) + len(line) + 1 > limit:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'

        # Add the last chunk if there is one
        if current_chunk:
            chunks.append(current_chunk.strip())

        # If any chunk is still too long, split it by words
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > limit:
                words = chunk.split(' ')
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 > limit:
                        final_chunks.append(current_chunk.strip())
                        current_chunk = word + ' '
                    else:
                        current_chunk += word + ' '
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
            else:
                final_chunks.append(chunk)

        return final_chunks
