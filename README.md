# CS 153 - Stylist Bot for UGC Creators

Bot Description:

Our Discord bot allows users to submit an Instagram post URL showcasing their outfit. It analyzes the image using the Gemini API to provide a style score and retrieves the post's engagement metrics (likes and comments). Based on these factors, the bot sends a personalized discount code via direct message, rewarding users for their fashion sense and social media influence.

Use Case:

This bot caters to fashion enthusiasts and influencers seeking feedback on their outfits and incentives for high engagement. By integrating fashion analysis with personalized rewards, it enhances user engagement and fosters brand loyalty within the fashion community. Another use case is it helps them scout UGC creators, and it also allows the brand to set trends which the audience can submit their posts to rate.

# FashionBot

A Discord bot that uses AI to analyze fashion outfits, provide feedback, and manage fashion trend challenges.

## Features

- AI-powered outfit analysis and feedback using Google's Gemini Vision API
- Fashion trend challenges with points and leaderboards
- Style competitions with voting and winners
- User chat history tracking for personalized responses
- Follow-up feedback functionality

## Commands

- **!submit** - Submit an outfit image for the current trend challenge
- **!feedback [question]** - Ask for more detailed feedback or advice about your last outfit submission
- **!trend** - View current trend challenge information
- **!points** - Check your current points
- **!leaderboard** - View the top users and their points
- **!competition** - View and participate in fashion competitions
- **!vote** - Vote for competition entries
- **!help** - Display help information

## Setup

1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run the bot with `python bot.py`

## Configuration

The bot requires the following environment variables:
- `DISCORD_TOKEN` - Your Discord bot token
- `GEMINI_API_KEY` - Your Google Gemini API key
