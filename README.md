# 🤖 AI Agentic Trading Swarm: Sentinel + Sniper + RL

> **A fully autonomous, multi-agent algorithmic trading system for Bitcoin Futures.**
> *By AAYUSH KUMAR*

![Project Status](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![AI](https://img.shields.io/badge/AI-Llama3%20%2B%20PPO-orange)

## 📖 Overview
This is not a standard trading bot. It is an **Agentic Swarm System** where three distinct AI agents collaborate to make high-probability trading decisions. It mimics a professional hedge fund desk by separating **Intuition (News)**, **Reflexes (Price Action)**, and **Risk Management (Reinforcement Learning)**.

The system requires **Full Confluence** between agents to execute a trade. If the News is bearish, the trade is blocked. If the Risk Boss senses volatility, the trade is vetoed.

---

## 🧠 The Swarm Architecture

### 1. The Sentinel (Sentiment Agent)
* **Role:** The Intuition.
* **Tech:** Llama 3 (via Ollama) + CryptoPanic API.
* **Function:** Scans real-time global news wires every 60 minutes. It uses a Large Language Model (LLM) to read headlines and determine the **Global Market Bias** (BULLISH, BEARISH, or NEUTRAL).

### 2. The Sniper (Technical Agent)
* **Role:** The Reflexes.
* **Tech:** Python + CCXT (Binance Futures).
* **Function:** Monitors price action in real-time (15m timeframe). It hunts for specific institutional patterns:
    * **Fair Value Gaps (FVG)**
    * **Momentum Confluence**
    * **Trend Alignment**

### 3. The Risk Boss (Reinforcement Learning Agent)
* **Role:** The Brain.
* **Tech:** Stable-Baselines3 (PPO Algorithm) + Gymnasium.
* **Function:** A Neural Network trained on **3 years of historical data**.
    * It does *not* predict price.
    * It predicts **Risk**.
    * It receives normalized market data (Volatility, Volume, Momentum) and decides the **Position Size** (0.5%, 1.0%, 2.0%, or **SKIP**).
    * **Unique Feature:** It has "Veto Power" to reject trades if market conditions look unsafe, even if the other agents want to buy.

---

## 🚀 Key Features & Uniqueness

* **Multi-Agent Confluence:** Unlike RSI/MACD bots, this system requires agreement from News, Price, and Risk models.
* **Robust Error Handling:** Built for 24/7 cloud deployment. Features auto-reconnect logic, API outage handling, and memory protection.
* **Adaptive Risk:** The Position Size is dynamic. In calm markets, it risks more. In chaos, it scales down or sits on its hands.
* **Privacy First:** Runs locally or on private VPS. No data is sent to third-party signal services.

---

## 🛠️ Installation

### Prerequisites
* Python 3.8+
* [Ollama](https://ollama.com/) (Running `llama3.2`)
* Binance Futures Account (Testnet supported)

### Setup
1.  **Clone the Repo:**
    ```bash
    git clone [https://github.com/yourusername/ai-trading-swarm.git](https://github.com/yourusername/ai-trading-swarm.git)
    cd ai-trading-swarm
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the Brains:**
    * Terminal 1: `ollama serve`
    * Terminal 2: `python main_swarm.py`

---

## 📊 Accuracy & Logic
* **Backtesting:** The Risk Agent was trained on 50,000 steps of historical simulation.
* **Normalization:** Inputs are normalized (Log Volume, % Change) to prevent neural network bias.
* **Safety Net:** The system defaults to "Demo Mode" to prevent accidental capital loss during testing.

## ⚠️ Disclaimer
*This software is for educational purposes only. Algorithmic trading involves significant risk. The author is not responsible for financial losses. Always test on Testnet for at least 30 days before deploying real capital.*
