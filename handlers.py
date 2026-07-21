import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database import (
    get_or_create_user, get_user_profile, get_user_settings,
    update_user_profile, update_user_settings, save_analysis, get_user_history
)
from openai_client import analyze_request, improve_response, generate_alternative

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PROMPT, WAITING_FOR_SETTING = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    user = update.effective_user
    get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = f"""👋 Welcome, {user.first_name}!

I'm your AI-powered request analyzer. I can:
• Analyze your requests with scores and risk assessment
• Generate professional responses
• Improve existing content
• Customize response style and settings

Use /help to see all available commands."""

    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler."""
    help_text = """📚 Available Commands:

/start - Start the bot
/help - Show this help message
/prompt - Analyze a new request
/profile - View/edit your profile
/settings - Manage bot settings
/test - Test with example request

🎯 How to use:
1. Send /prompt to start analyzing
2. Enter your request text
3. Get analysis with score, risks, and response
4. Use buttons to improve or regenerate

💡 Tips:
• Click "Новый вариант" for alternative responses
• Click "Улучшить" for enhanced version
• Click "Коротко" for concise version
• Click "Длиннее" for detailed version"""

    await update.message.reply_text(help_text)


async def prompt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt command - start analysis workflow."""
    user_id = update.effective_user.id
    get_or_create_user(user_id, update.effective_user.username, 
                      update.effective_user.first_name, update.effective_user.last_name)
    
    await update.message.reply_text(
        "📝 Enter your request for analysis:\n\n"
        "I'll analyze it, provide a score, identify risks, and generate a professional response."
    )
    return WAITING_FOR_PROMPT


async def process_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the user's request."""
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # Get user profile
    profile = get_user_profile(user_id)
    style = profile.response_style if profile else "professional"
    
    # Show processing message
    processing_msg = await update.message.reply_text("⏳ Analyzing your request...")
    
    try:
        # Analyze using GPT
        analysis = analyze_request(user_text, style)
        
        # Save to database
        save_analysis(user_id, user_text, analysis["score"], 
                     str(analysis["risks"]), analysis["response"])
        
        # Format response
        risks_text = "\n".join([f"• {risk}" for risk in analysis["risks"]])
        score_emoji = "🔴" if analysis["score"] < 40 else "🟡" if analysis["score"] < 70 else "🟢"
        
        result_text = f"""
{score_emoji} <b>Score: {analysis["score"]}/100</b>

⚠️ <b>Risks:</b>
{risks_text}

✅ <b>Professional Response:</b>
{analysis["response"]}
"""
        
        # Create inline buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Новый вариант", callback_data=f"alt_{user_id}"),
             InlineKeyboardButton("✨ Улучшить", callback_data=f"improve_{user_id}")],
            [InlineKeyboardButton("📏 Коротко", callback_data=f"concise_{user_id}"),
             InlineKeyboardButton("📚 Длиннее", callback_data=f"detailed_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Delete processing message and send result
        await processing_msg.delete()
        await update.message.reply_text(result_text, 
                                       parse_mode=ParseMode.HTML,
                                       reply_markup=reply_markup)
        
        # Store analysis in context for button handlers
        context.user_data["last_analysis"] = analysis
        context.user_data["last_prompt"] = user_text
        
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}")
        await processing_msg.delete()
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    return ConversationHandler.END


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show and manage user profile."""
    user_id = update.effective_user.id
    user = update.effective_user
    
    profile = get_user_profile(user_id)
    
    profile_text = f"""
👤 <b>Your Profile</b>

<b>Name:</b> {user.first_name} {user.last_name or ""}
<b>Username:</b> @{user.username or "N/A"}
<b>Telegram ID:</b> {user_id}

⚙️ <b>Preferences</b>
<b>Language:</b> {profile.language if profile else "en"}
<b>Response Style:</b> {profile.response_style if profile else "professional"}
<b>Tone:</b> {profile.tone if profile else "formal"}
"""
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="lang_select"),
         InlineKeyboardButton("🎭 Change Style", callback_data="style_select")],
        [InlineKeyboardButton("🎤 Change Tone", callback_data="tone_select")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(profile_text, 
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=reply_markup)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show and manage user settings."""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    
    settings_text = f"""
⚙️ <b>Bot Settings</b>

<b>Notifications:</b> {'✅ Enabled' if settings.notifications_enabled else '❌ Disabled'}
<b>Auto-improve:</b> {'✅ Enabled' if settings.auto_improve else '❌ Disabled'}
<b>Max Response Length:</b> {settings.max_response_length} characters
"""
    
    keyboard = [
        [InlineKeyboardButton("🔔 Toggle Notifications", callback_data="toggle_notif"),
         InlineKeyboardButton("🤖 Toggle Auto-improve", callback_data="toggle_auto")],
        [InlineKeyboardButton("📏 Set Max Length", callback_data="set_length")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(settings_text,
                                   parse_mode=ParseMode.HTML,
                                   reply_markup=reply_markup)


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test command with example request."""
    user_id = update.effective_user.id
    get_or_create_user(user_id, update.effective_user.username,
                      update.effective_user.first_name, update.effective_user.last_name)
    
    test_text = "I would like to request a meeting with the team to discuss the Q3 project roadmap and get feedback on our current progress."
    
    processing_msg = await update.message.reply_text("⏳ Analyzing test request...")
    
    try:
        analysis = analyze_request(test_text, "professional")
        save_analysis(user_id, test_text, analysis["score"],
                     str(analysis["risks"]), analysis["response"])
        
        risks_text = "\n".join([f"• {risk}" for risk in analysis["risks"]])
        score_emoji = "🔴" if analysis["score"] < 40 else "🟡" if analysis["score"] < 70 else "🟢"
        
        result_text = f"""
{score_emoji} <b>Score: {analysis["score"]}/100</b>

⚠️ <b>Risks:</b>
{risks_text}

✅ <b>Professional Response:</b>
{analysis["response"]}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Новый вариант", callback_data=f"alt_{user_id}"),
             InlineKeyboardButton("✨ Улучшить", callback_data=f"improve_{user_id}")],
            [InlineKeyboardButton("📏 Коротко", callback_data=f"concise_{user_id}"),
             InlineKeyboardButton("📚 Длиннее", callback_data=f"detailed_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.delete()
        await update.message.reply_text(result_text,
                                       parse_mode=ParseMode.HTML,
                                       reply_markup=reply_markup)
        
        context.user_data["last_analysis"] = analysis
        context.user_data["last_prompt"] = test_text
        
    except Exception as e:
        logger.error(f"Error in test command: {str(e)}")
        await processing_msg.delete()
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    action = query.data.split("_")[0]
    last_analysis = context.user_data.get("last_analysis")
    last_prompt = context.user_data.get("last_prompt")
    
    if not last_analysis or not last_prompt:
        await query.edit_message_text("❌ Session expired. Please use /prompt again.")
        return
    
    processing_msg = await query.edit_message_text("⏳ Processing...")
    
    try:
        if action == "alt":
            new_response = generate_alternative(last_prompt, "professional")
        elif action == "improve":
            new_response = improve_response(last_prompt, last_analysis["response"], "general")
        elif action == "concise":
            new_response = improve_response(last_prompt, last_analysis["response"], "concise")
        elif action == "detailed":
            new_response = improve_response(last_prompt, last_analysis["response"], "detailed")
        else:
            new_response = last_analysis["response"]
        
        result_text = f"""
✅ <b>Updated Response:</b>
{new_response}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Новый вариант", callback_data=f"alt_{user_id}"),
             InlineKeyboardButton("✨ Улучшить", callback_data=f"improve_{user_id}")],
            [InlineKeyboardButton("📏 Коротко", callback_data=f"concise_{user_id}"),
             InlineKeyboardButton("📚 Длиннее", callback_data=f"detailed_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(result_text,
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=reply_markup)
        
        context.user_data["last_analysis"]["response"] = new_response
        
    except Exception as e:
        logger.error(f"Error in button handler: {str(e)}")
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
