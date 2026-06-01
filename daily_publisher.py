import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Honest Talk About Relationships — What No One Tells You",
        "Why Your Ex Keeps Coming Back — The Real Reason",
        "How to Level Up Your Life in 2025",
        "Red Flags You Keep Ignoring in Relationships",
        "The Truth About Money Nobody Teaches You",
        "Signs You're Healing From a Breakup Without Realizing It",
        "How to Stop Overthinking Everything",
        "Things I Wish I Knew Before My Last Relationship",
        "You Deserve Better — And Here's Why",
        "The Hardest Lesson Life Taught Me This Year",
        "Money Mistakes That Keep You Broke",
        "How to Set Boundaries Without Feeling Guilty",
        "Signs You're Growing and Everyone Around You Isn't",
        "Real Talk About Loneliness and Finding Yourself",
        "Why Being Single Is Actually Your Superpower",
    ]

    fallback_descriptions = [
        "Let's be real for a second — relationships are harder than anyone tells you. It's not all romantic dates and cute texts. It's communication, compromise, and knowing when to walk away. Whether you're single, taken, or healing, this one hits different. Drop a heart if you've been through this and came out stronger. ❤️ #relationships #realtalk #lifelessons #growth #datingadvice #selflove #healing #breakup #love #mindset #relationshipadvice #movingon",
        "Ever wonder why your ex keeps showing up? It might not be love. Sometimes people come back because they miss how you made them feel, not because they've changed. Knowing the difference saves you so much pain. Protect your peace and stop letting the past distract you from what's meant for you. Like if you needed this reminder today. ✨ #exback #breakup #healingjourney #selfworth #relationshipadvice #movingon #growthmindset #love #dating #realtalk #boundaries",
        "Leveling up isn't just about money — it's about your mindset, your circle, your daily habits, and how you show up for yourself. Small changes every day lead to massive results over time. Cut the distractions, focus on your goals, and watch everything shift. Comment one thing you're doing to level up this year! 🚀 #levelup #growthmindset #selfimprovement #goals #motivation #success #moneymindset #lifestyle #discipline #hustle",
        "We all have that one friend who keeps falling for the same type. Or maybe that friend is you. Red flags don't disappear, they just get harder to see when you're attached. Trust your gut the first time — it's usually right. Save this as a reminder to never settle for less than you deserve. 💯 #redflags #datingadvice #relationships #selflove #warningsigns #love #dating #toxicrelationships #boundaries",
        "Nobody teaches you how money actually works. Not in school, not at home. You're just expected to figure it out. Budgeting, investing, saving, avoiding debt — these are skills you have to learn on your own. Start now, even if it's small. Your future self will thank you. Like if you wish they taught this in school! 💰 #moneytips #financialliteracy #personalfinance #budgeting #investing #wealth #moneymindset #success #education #lifelessons",
        "Healing isn't linear. Some days you're fine, other days a song hits different and you're back to square one. But here's the thing — if you're feeling it, you're healing. The fact that it still hurts means it mattered. Be patient with yourself. Give yourself the grace you'd give a friend going through the same thing. Drop a 🦋 if you're on your healing journey too.",
        "Overthinking is just your brain trying to protect you from getting hurt again. But it's keeping you stuck in a loop that doesn't serve you. Train your mind to focus on what you can control and let go of what you can't. It's not easy but it's worth it. Double tap if you needed this reminder. 🧠 #overthinking #anxietyrelief #mentalhealth #mindset #selfawareness #growth #healing #peaceofmind #lettinggo",
        "Looking back at my last relationship, there were so many things I wish someone had told me. That love shouldn't feel like a battle. That you shouldn't have to shrink yourself to fit into someone else's life. That walking away doesn't mean you failed. Learn from my mistakes so you don't have to make them yourself. 💔 #relationships #lessonslearned #datingadvice #breakup #selflove #growth #healing #love #realtalk",
        "You deserve someone who chooses you every single day, not just when it's convenient. Not someone who makes you question your worth or leaves you wondering where you stand. Real love doesn't confuse you. Don't settle for breadcrumbs when you deserve the whole bakery. Like if you agree. 💕 #selflove #knowyourworth #relationships #datingadvice #love #boundaries #healing",
        "Life has a way of humbling you right when you think you have it all figured out. But those hard moments? They teach you more than any easy day ever could. Growth is painful but so worth it. Here's what I learned this year about resilience, letting go, and trusting the process. Drop a 🌱 if you're growing through it.",
        "The biggest money mistake? Thinking you have to be rich to start investing. Or that saving a little doesn't matter. Small habits compound. Skip the coffee runs, automate your savings, invest even $20 a week, and stop trying to keep up with people who aren't paying your bills. Your wallet will thank you. Save this for later! 📈 #moneytips #financialfreedom #budgeting #wealthbuilding #investing #personalfinance #savingmoney",
        "Setting boundaries isn't rude — it's self-respect. You're allowed to say no. You're allowed to protect your energy. You're allowed to walk away from people who make you feel small. The right people will respect your boundaries. The wrong ones will get offended. That's how you know the difference. 💪 #boundaries #selflove #mentalhealth #growth #relationships #selfrespect #realtalk",
        "Ever feel like you're outgrowing your friends? It's not a bad thing — it means you're evolving. Not everyone is meant to come with you to the next chapter. Some people are only in your life for a season. Let them go with love and keep moving forward. The right circle will find you. Comment if you've been through this. 🌟 #growth #friendship #evolution #movingon #selfgrowth #mindset #lifelessons",
        "Loneliness hits different when you're surrounded by people but still feel alone. But here's the truth I've learned — being alone doesn't have to be lonely. It's a chance to get to know yourself again. To figure out what you actually want. To become someone you're proud to be alone with. This chapter is necessary. Trust the process. 🕯️ #loneliness #selflove #healing #solitude #growth #mentalhealth #realtalk",
        "Society makes you feel like being single means something's wrong with you. But some of the most transformative years of your life happen when you're alone. You get to figure out who you are without anyone else's influence. You learn to enjoy your own company. You raise your standards. Single isn't a curse — it's a blessing in disguise. 💫 #singlegirl #selflove #empowerment #dating #relationships #growth #independence",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "honest and relatable — speak like a close friend giving real advice",
        "thought-provoking and real — make people stop scrolling and think about their own life",
        "warming and encouraging — make viewers feel understood and less alone",
        "bold and unfiltered — say the things people are afraid to say out loud",
        "story-driven and personal — share real experiences and lessons learned",
        "reflective and deep — ask questions that make people pause and reflect",
        "empowering and uplifting — give viewers a push to level up their life",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Valeria Solverde'. "
        f"The page covers real talk about relationships, breakups, life lessons, money, personal growth, "
        f"and everything in between. It's authentic, relatable, and speaks directly to the heart. "
        f"Speak as a wise, authentic friend who's been through it all and shares honest advice. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"- Like if this hit different! "
        f"- Comment your thoughts below! "
        f"- Share this with someone who needs to hear it! "
        f"- Follow Valeria Solverde for more real talk! "
        f"Include relevant hashtags in ALL LOWERCASE such as #relationships #realtalk #lifelessons #growth #selflove #datingadvice #healing #breakup #love #mindset #moneytips #personalgrowth #advice #motivation. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["relationships", "lifelessons", "realtalk", "advice", "selflove", "dating", "breakup", "personalgrowth", "motivation", "mindset", "moneytips", "healing", "love", "growth", "valeria solverde"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
