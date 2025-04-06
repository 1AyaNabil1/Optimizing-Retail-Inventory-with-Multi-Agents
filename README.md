# SmartStock AI – Multi-Agent Retail Inventory Optimization 🚀

![Hackathon Banner](img/image.png)

## Overview 📖
**SmartStock AI** is a collaborative multi-agent system built to intelligently optimize retail inventory management. Designed during the **"Hack the Future: A Gen AI Sprint Powered by Data"** hackathon, it addresses critical retail challenges like stockouts, overstocking, and inefficient supply chains using intelligent agents and AI-driven forecasts.

By combining real-time collaboration and predictive AI, SmartStock AI dynamically balances product availability and inventory costs across stores, warehouses, and suppliers—ensuring smarter, faster, and leaner operations.

---

## ❗ Problem Statement
Retail businesses suffer from:

- **Stockouts** – Lost revenue from empty shelves 😞
- **Overstocking** – Excess inventory costs and space issues 💸
- **Manual Processes** – Delayed forecasting and inefficient operations ⏳

**Our Goal**: Build an AI-powered, multi-agent system that automates demand prediction, inventory management, and price adjustment to boost efficiency and cut operational costs.

---

## 🌟 The SmartStock AI System

The system is built around **five core agents**:

1. **🧠 Demand Prediction Agent**  
   Predicts future product demand using historical data, trends, and seasonality.

2. **🏪 Store Agent**  
   Tracks real-time inventory, requests restocks, and adjusts prices for slow-moving items.

3. **🏭 Warehouse Agent**  
   Allocates stock across stores and triggers restock requests to suppliers.

4. **🚚 Supplier Agent**  
   Coordinates product replenishment based on warehouse alerts and lead times.

5. **🧑‍🤝‍🧑 Customer Agent**  
   Learns customer preferences from anonymized data to refine predictions and promotions.

---

## ✨ Key Features

- 🔁 **Proactive Restocking**: Anticipates needs before critical levels hit.  
- 📉 **Cost Optimization**: Reduces overstocking through AI-aligned forecasting.  
- 🏷️ **Dynamic Pricing**: Adapts pricing in real-time based on product demand and turnover.  
- ⚡ **Real-Time Coordination**: Seamless communication among agents using shared state.

---

## 📂 Dataset Overview

Located in the `data/` directory:

| File | Description |
|------|-------------|
| `demand_forecasting.csv` | Sales data and customer segments |
| `inventory_monitoring.csv` | Stock levels and warehouse capacities |
| `pricing_optimization.csv` | Historical price data and margins |

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.13 🐍
- Install dependencies: ```bash
pip install pandas ```  📦

### Folder Structure:
```bash
SmartStockAI/
├── data/
│   ├── demand_forecasting.csv
│   ├── inventory_monitoring.csv
│   └── pricing_optimization.csv
├── main.py
├── demand_agent.py
├── store_agent.py
├── warehouse_agent.py
├── supplier_agent.py
├── customer_agent.py
├── database.py
└── README.md
```
---
## ▶️ How to Run
**1. Run the Simulation**
```bash
python main.py
```
This runs a step-by-step simulation where agents interact to manage demand and supply.

**2. Run the Database Demo**
```bash
python database.py
```
Demonstrates inventory updates using a local SQLite simulation.

---
## 📌 Code Components
- `main.py`: Controls simulation loop and orchestrates agent logic.

* `demand_agent.py`: Contains logic for each specific agent.

* `database.py`: Simulates real-time inventory updates in SQLite.
---
## ⚙️ Technical Stack
* **Language**: Python

* **Data Handling**: pandas

* **Database**: In-memory SQLite

* **AI Models**: Simple trend forecasting (extendable to LSTM or Ollama LLM)
---
## 📊 Expected Impact
* 📈 **Sales Boost**: 15–20% increase by preventing stockouts

* 💰 **Cost Savings**: 10–15% reduction in holding costs

* 🔄 **Efficiency Gains**: 25% improvement in supply chain response time
---
## 🚀 Future Enhancements
* Real-world data ingestion from APIs and POS systems

* Advanced AI (e.g., LSTM, Ollama, Graph Neural Nets)

* Integration with agent frameworks like SPADE or Mesa

* Web-based UI dashboard for live tracking (under maintanence)
---
## 🎯 Hackathon Context
* **Team**: AyaNeXus (Solo Participant: Aya Nabil)

* **Project Name**: SmartStock AI

* **Submission File**: AyaNeXus_SmartStockAI.pptx

* **Date**: April 6, 2025

* **Event**: Hack the Future: A Gen AI Sprint Powered by Data
---
## 🙌 Acknowledgments
Hackathon organizers for providing initial datasets and problem statements.

Python open-source community for tools that made rapid prototyping possible.

👋 For feedback or questions, contact ayanabil297@gmail.com

Happy Hacking! 💻✨