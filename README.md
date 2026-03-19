# Real-Time Operational Intelligence System

A real-time operational intelligence dashboard that simulates geographically grounded incident activity, detects anomalous patterns, and surfaces actionable alerts for decision support.

---

## Overview

This system models how modern operational platforms transform continuous streams of event data into actionable intelligence.

The application ingests a live stream of simulated incidents anchored to real-world geographic hubs, evaluates activity using weighted scoring and recency-based logic, and generates prioritized alerts to highlight abnormal patterns.

The goal is to reduce cognitive load and support rapid situational awareness in time-sensitive environments.

---

## Key Capabilities

- Real-time event simulation tied to geographic locations  
- Interactive map visualization of incident activity  
- Weighted threat scoring based on:
  - Event frequency
  - Location priority
  - Recency of activity  
- Multi-level alert classification (LOW, MEDIUM, HIGH)  
- Alert cooldown logic to prevent noise and alert fatigue  
- Temporal analysis (activity over time)  
- Incident type distribution insights  
- Identification of highest-risk operational area  

---

## System Design

### Data Ingestion
Events are generated continuously and associated with real-world locations (transport, logistics, and infrastructure hubs).

### Processing
Each event is evaluated using a weighted scoring model that incorporates:
- Event type severity
- Location importance
- Time decay (recent events have higher impact)

### Alerting
The system classifies activity into multiple threat levels and applies cooldown logic to avoid redundant alerts.

### Visualization
The dashboard presents:
- Live incident feed  
- Geographic activity map  
- Threat level metrics  
- Trend and distribution analytics  

---

## Tech Stack

- Python  
- Streamlit  
- Pandas  
- PyDeck (geospatial visualization)  

---

## Running the Application

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
