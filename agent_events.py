# -*- coding: utf-8 -*-
"""
Created on Wed May  6 19:39:36 2026

@author: ydhor
""" 

# create_agent_events.py

import os
import pandas as pd

#os.makedirs("data", exist_ok=True)

agent_events = pd.DataFrame(columns=[
    "event_id",
    "timestamp",
    "claim_id",
    "agent_name",
    "event_type",
    "input_summary",
    "decision",
    "output_summary",
    "next_agent",
    "status"
])

agent_events.to_csv("./data/agent_events.csv", index=False)

print("Created agent_events.csv")