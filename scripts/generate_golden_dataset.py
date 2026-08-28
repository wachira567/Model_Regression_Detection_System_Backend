import json
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "golden-dataset", "email_classifier_v1.json")

NEW_CASES = [
    # Billing
    {"input": {"email_text": "I see a charge of $15 on my credit card but I thought the first month was free?"}, "expected_output": {"category": "billing", "summary": "Customer is questioning a charge during their expected free trial."}, "difficulty": "moderate", "tags": ["billing", "trial", "confusion"]},
    {"input": {"email_text": "Please cancel my subscription and refund my last payment. I haven't used the app in months."}, "expected_output": {"category": "billing", "summary": "Customer wants to cancel subscription and requests a refund for previous payment."}, "difficulty": "easy", "tags": ["billing", "refund", "cancel"]},
    {"input": {"email_text": "How do I update my credit card info? It keeps failing."}, "expected_output": {"category": "billing", "summary": "Customer needs help updating their failing credit card information."}, "difficulty": "easy", "tags": ["billing", "update_payment"]},
    {"input": {"email_text": "You guys billed me 3 times today! Fix this NOW or I'm calling my bank."}, "expected_output": {"category": "billing", "summary": "Customer is angry about being charged three times in one day."}, "difficulty": "easy", "tags": ["billing", "angry", "multiple_charges"]},
    {"input": {"email_text": "i payed but still no pro features :("}, "expected_output": {"category": "billing", "summary": "Customer paid for pro features but they are not activated."}, "difficulty": "moderate", "tags": ["billing", "account_sync", "typos"]},
    {"input": {"email_text": "Can I get an invoice for last month's purchase for my company?"}, "expected_output": {"category": "billing", "summary": "Customer is requesting an invoice for a past purchase."}, "difficulty": "easy", "tags": ["billing", "invoice"]},
    {"input": {"email_text": "Your pricing page says $10 but my receipt says $12. What gives? Is it taxes?"}, "expected_output": {"category": "billing", "summary": "Customer is asking why their receipt amount is higher than the advertised price."}, "difficulty": "moderate", "tags": ["billing", "pricing", "taxes"]},
    {"input": {"email_text": "I got a new card, old one was stolen. Need to pay my bill so I don't lose access."}, "expected_output": {"category": "billing", "summary": "Customer needs to update payment method due to a stolen card."}, "difficulty": "easy", "tags": ["billing", "payment_update"]},
    {"input": {"email_text": "Refund me. Now."}, "expected_output": {"category": "billing", "summary": "Customer is demanding a refund."}, "difficulty": "easy", "tags": ["billing", "short", "refund"]},
    {"input": {"email_text": "Is there a student discount available?"}, "expected_output": {"category": "billing", "summary": "Customer is asking about a student discount."}, "difficulty": "easy", "tags": ["billing", "discount"]},
    {"input": {"email_text": "My coupon code 'SUMMER20' isn't working at checkout."}, "expected_output": {"category": "billing", "summary": "Customer is reporting a broken coupon code at checkout."}, "difficulty": "easy", "tags": ["billing", "coupon"]},
    {"input": {"email_text": "I tried to buy the annual plan but it says 'Gateway Error 502'. Did my payment go through?"}, "expected_output": {"category": "billing", "summary": "Customer experienced a gateway error during purchase and wants to know if it succeeded."}, "difficulty": "hard", "tags": ["billing", "technical", "payment_error"]},
    
    # Technical
    {"input": {"email_text": "The Android app crashes every time I try to open the settings menu."}, "expected_output": {"category": "technical", "summary": "Customer reports the Android app crashes when opening settings."}, "difficulty": "easy", "tags": ["technical", "crash", "android"]},
    {"input": {"email_text": "When I export to PDF, the fonts are all messed up and unreadable. Im on Mac OS 14."}, "expected_output": {"category": "technical", "summary": "Customer reports unreadable fonts when exporting to PDF on macOS."}, "difficulty": "moderate", "tags": ["technical", "export", "bug"]},
    {"input": {"email_text": "site is down"}, "expected_output": {"category": "technical", "summary": "Customer is reporting that the website is down."}, "difficulty": "easy", "tags": ["technical", "short", "outage"]},
    {"input": {"email_text": "I'm getting a 404 error when I click the link in my password reset email."}, "expected_output": {"category": "technical", "summary": "Customer gets a 404 error clicking the password reset link."}, "difficulty": "moderate", "tags": ["technical", "account", "broken_link"]},
    {"input": {"email_text": "Why is the API rate limiting me at 50 req/sec when my plan says 100?"}, "expected_output": {"category": "technical", "summary": "Customer is being rate-limited below their expected plan limits."}, "difficulty": "moderate", "tags": ["technical", "api", "rate_limit"]},
    {"input": {"email_text": "Can't connect to server. Error code: ERR_CONNECTION_REFUSED. Pls advise."}, "expected_output": {"category": "technical", "summary": "Customer cannot connect to the server and receives a connection refused error."}, "difficulty": "easy", "tags": ["technical", "connection"]},
    {"input": {"email_text": "The dark mode toggle doesn't save when I refresh the page."}, "expected_output": {"category": "technical", "summary": "Customer reports dark mode preference is not saving across page refreshes."}, "difficulty": "easy", "tags": ["technical", "ui", "bug"]},
    {"input": {"email_text": "Whenever I type in the search bar, the whole page lags for 5 seconds."}, "expected_output": {"category": "technical", "summary": "Customer is experiencing severe lag when typing in the search bar."}, "difficulty": "easy", "tags": ["technical", "performance"]},
    {"input": {"email_text": "Is the webhook payload missing the 'user_id' field intentionally or is this a bug?"}, "expected_output": {"category": "technical", "summary": "Customer is asking if a missing field in the webhook payload is intentional."}, "difficulty": "hard", "tags": ["technical", "developer", "webhook"]},
    {"input": {"email_text": "Your iOS app drained 40% of my battery in one hour. Fix this trash."}, "expected_output": {"category": "technical", "summary": "Customer is complaining about excessive battery drain on the iOS app."}, "difficulty": "moderate", "tags": ["technical", "performance", "battery", "angry"]},
    {"input": {"email_text": "Images aren't loading on the dashboard. Just seeing broken image icons."}, "expected_output": {"category": "technical", "summary": "Customer reports that images are failing to load on the dashboard."}, "difficulty": "easy", "tags": ["technical", "ui", "images"]},
    {"input": {"email_text": "I tried updating to v2.4.1 but the installer hangs at 99%."}, "expected_output": {"category": "technical", "summary": "Customer reports the installer hangs at 99% when updating."}, "difficulty": "easy", "tags": ["technical", "install", "hang"]},
    
    # Account
    {"input": {"email_text": "I forgot my password and no longer have access to my old email address. How can I log in?"}, "expected_output": {"category": "account", "summary": "Customer lost access to their old email and needs help recovering their account."}, "difficulty": "hard", "tags": ["account", "recovery", "no_access"]},
    {"input": {"email_text": "Can you delete my account and all associated data under GDPR?"}, "expected_output": {"category": "account", "summary": "Customer is requesting account deletion under GDPR."}, "difficulty": "easy", "tags": ["account", "deletion", "gdpr"]},
    {"input": {"email_text": "I want to change my username from 'skaterboi' to 'johndoe'."}, "expected_output": {"category": "account", "summary": "Customer wants to change their username."}, "difficulty": "easy", "tags": ["account", "username"]},
    {"input": {"email_text": "Please invite my colleague sarah@example.com to my organization workspace."}, "expected_output": {"category": "account", "summary": "Customer is requesting to invite a colleague to their workspace."}, "difficulty": "easy", "tags": ["account", "invite", "workspace"]},
    {"input": {"email_text": "I'm the admin but I can't access the billing tab. It says unauthorized."}, "expected_output": {"category": "account", "summary": "Customer with admin rights is receiving an unauthorized error accessing billing."}, "difficulty": "moderate", "tags": ["account", "billing", "permissions"]},
    {"input": {"email_text": "My account was banned for spam but I swear I was hacked! Please unban me."}, "expected_output": {"category": "account", "summary": "Customer is appealing a spam ban, claiming they were hacked."}, "difficulty": "moderate", "tags": ["account", "ban_appeal", "hacked"]},
    {"input": {"email_text": "How do I setup 2FA? The QR code isn't scanning on Google Authenticator."}, "expected_output": {"category": "account", "summary": "Customer is having trouble scanning the 2FA QR code."}, "difficulty": "moderate", "tags": ["account", "technical", "2fa"]},
    {"input": {"email_text": "Make me admin."}, "expected_output": {"category": "account", "summary": "Customer is requesting admin privileges."}, "difficulty": "easy", "tags": ["account", "short", "permissions"]},
    {"input": {"email_text": "I created two accounts by mistake. Can you merge them?"}, "expected_output": {"category": "account", "summary": "Customer is asking to merge two duplicate accounts."}, "difficulty": "easy", "tags": ["account", "merge"]},
    {"input": {"email_text": "Can I transfer ownership of this workspace to my manager?"}, "expected_output": {"category": "account", "summary": "Customer wants to transfer workspace ownership to their manager."}, "difficulty": "easy", "tags": ["account", "ownership"]},
    {"input": {"email_text": "I didn't receive the email confirmation link. Resend it?"}, "expected_output": {"category": "account", "summary": "Customer needs the account confirmation email resent."}, "difficulty": "easy", "tags": ["account", "verification"]},
    {"input": {"email_text": "Where do I update my shipping address?"}, "expected_output": {"category": "account", "summary": "Customer is asking how to update their shipping address."}, "difficulty": "easy", "tags": ["account", "profile_update"]},
    
    # General / Ambiguous / Mixed
    {"input": {"email_text": "Hey, what are your business hours? I want to call you."}, "expected_output": {"category": "general", "summary": "Customer is asking for business hours and a phone number."}, "difficulty": "easy", "tags": ["general", "contact_info"]},
    {"input": {"email_text": "Do you guys have a roadmap for 2027? Curious about AI features."}, "expected_output": {"category": "general", "summary": "Customer is asking about the product roadmap for 2027 and AI features."}, "difficulty": "easy", "tags": ["general", "roadmap"]},
    {"input": {"email_text": "I really love your product, it changed my life! Thanks!"}, "expected_output": {"category": "general", "summary": "Customer is sending positive feedback and gratitude."}, "difficulty": "easy", "tags": ["general", "feedback", "praise"]},
    {"input": {"email_text": "asdfasdfasdfasdf"}, "expected_output": {"category": "general", "summary": "Customer sent an unintelligible message."}, "difficulty": "hard", "tags": ["general", "gibberish", "noise"]},
    {"input": {"email_text": "Who is the CEO of your company? I am a reporter for TechCrunch."}, "expected_output": {"category": "general", "summary": "Reporter is asking for the CEO's name for an article."}, "difficulty": "moderate", "tags": ["general", "pr", "media"]},
    {"input": {"email_text": "Can I get a free t-shirt?"}, "expected_output": {"category": "general", "summary": "Customer is asking for free company merchandise."}, "difficulty": "easy", "tags": ["general", "swag"]},
    {"input": {"email_text": "Are you hiring software engineers? I attached my resume."}, "expected_output": {"category": "general", "summary": "Customer is inquiring about software engineering jobs and attaching a resume."}, "difficulty": "easy", "tags": ["general", "hiring"]},
    {"input": {"email_text": "hola, como estas? no hablo ingles"}, "expected_output": {"category": "general", "summary": "Customer is speaking Spanish and stating they do not speak English."}, "difficulty": "moderate", "tags": ["general", "foreign_language"]},
    {"input": {"email_text": "I want to speak to a human. Give me a phone number."}, "expected_output": {"category": "general", "summary": "Customer is demanding a phone number to speak with a human representative."}, "difficulty": "easy", "tags": ["general", "escalation"]},
    {"input": {"email_text": "Is this service HIPAA compliant? We are a healthcare startup."}, "expected_output": {"category": "general", "summary": "Customer is asking if the service is HIPAA compliant for healthcare use."}, "difficulty": "moderate", "tags": ["general", "compliance", "hipaa"]},
    {"input": {"email_text": "I saw your ad on Facebook and it was offensive. Take it down."}, "expected_output": {"category": "general", "summary": "Customer is complaining about an offensive Facebook ad."}, "difficulty": "moderate", "tags": ["general", "feedback", "marketing"]},
    {"input": {"email_text": "What is the meaning of life?"}, "expected_output": {"category": "general", "summary": "Customer is asking a philosophical, non-product related question."}, "difficulty": "hard", "tags": ["general", "joke", "off_topic"]}
]

def generate():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Could not find dataset at {DATASET_PATH}")
        return

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    existing_cases = data.get("test_cases", [])
    start_idx = len(existing_cases) + 1
    
    for i, case in enumerate(NEW_CASES):
        case_id = f"TC{str(start_idx + i).zfill(3)}"
        case["id"] = case_id
        if "notes" not in case:
            case["notes"] = "Auto-generated test case for expanded coverage."
        existing_cases.append(case)
        
    data["test_cases"] = existing_cases
    
    with open(DATASET_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully added {len(NEW_CASES)} new cases. Total cases: {len(data['test_cases'])}")

if __name__ == "__main__":
    generate()
