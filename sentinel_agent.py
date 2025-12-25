import requests
import warnings
from langchain_ollama import OllamaLLM
import urllib3

# --- CONFIGURATION ---
API_KEY = ''  
CURRENCY = 'BTC'
MODEL_NAME = "llama3.2" 

# --- DISABLE SSL WARNINGS ---
# We are turning off the security warnings so your console stays clean
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_crypto_news():
    """Fetches top 5 recent news headlines from CryptoPanic V2 API."""
    
    url = (
        f"https://cryptopanic.com/api/developer/v2/posts/"
        f"?auth_token={API_KEY}"
        f"&currencies={CURRENCY}"
        f"&kind=news"
        f"&public=true"
    )
    
    try:
        print(f"Connecting to: {url} ...")
        
        # --- THE FIX IS HERE ---
        # verify=False tells Python to ignore the "Expired Certificate" error
        response = requests.get(url, verify=False)
        
        if response.status_code != 200:
            print(f"API Error! Status: {response.status_code}")
            return None
            
        data = response.json()
        
        headlines = []
        if 'results' in data:
            for post in data['results'][:5]: 
                title = post['title']
                
                # extracting source domain if available
                source = "Unknown"
                if 'source' in post and 'domain' in post['source']:
                    source = post['source']['domain']
                
                headlines.append(f"- [{source}] {title}")
        
        return "\n".join(headlines)
    
    except Exception as e:
        print(f"Critical Error: {e}")
        return None

def analyze_sentiment(headlines):
    """Sends headlines to Llama 3 for a decision."""
    # Safety check: if no headlines, return Neutral
    if not headlines:
        return "NEUTRAL"

    llm = OllamaLLM(model=MODEL_NAME)
    
    prompt = f"""
    You are a professional Crypto Trading Analyst. 
    Analyze the following recent news headlines for Bitcoin (BTC):
    
    {headlines}
    
    Based ONLY on these headlines, determine the immediate market sentiment.
    You must respond with EXACTLY one word: "BULLISH", "BEARISH", or "NEUTRAL".
    Do not explain. Just the word.
    """
    
    print("\n--- AI Thinking... ---")
    try:
        response = llm.invoke(prompt)
        return response.strip().upper()
    except Exception as e:
        print(f"Ollama Error: {e}")
        return "NEUTRAL"

if __name__ == "__main__":
    print(f"Fetching news for {CURRENCY}...")
    news = get_crypto_news()
    
    if news:
        print(f"\nTop Headlines:\n{news}")
        decision = analyze_sentiment(news)
        print(f"\n>>> SENTINEL AGENT DECISION: {decision} <<<")
        
        if "BULLISH" in decision:
            print("Action: ALLOW Long Trades. INCREASE Risk.")
        elif "BEARISH" in decision:
            print("Action: BLOCK Long Trades. LOOK for Shorts.")
        else:
            print("Action: STANDARD Risk.")
    else:

        print("Failed to get news.")
