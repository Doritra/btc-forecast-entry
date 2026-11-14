"""
This module forecasts BTC prices (e.g. 4 hours ahead) based on historical per-minute prices and drift analysis.
"""

import os
import json

def compute_forecast(prices, horizon_minutes):
    """
    Computes the forecast price based on the given prices list and horizon minutes.
    Algorithm:
    - L = prices[-1]
    - if length > 61: d60 = (L - prices[-61]) / 60 else d60 = 0
    - if length > 31: d30 = (L - prices[-31]) / 30 else d30 = 0
    - d = 0.5 * d30 + 0.5 * d60
    - adjustment = d * horizon_minutes * 0.4
    - clamp adjustment to at most 0.004 * L in absolute value
    - forecast = L + adjustment
    - Round the price to 5 decimals, clamp to (0.00001, 9999999.99999).
    """
    if not prices:
        return 0.0
    
    length = len(prices)
    L = prices[-1]
    
    d60 = (L - prices[-61]) / 60.0 if length > 61 else 0.0
    d30 = (L - prices[-31]) / 30.0 if length > 31 else 0.0
    
    d = 0.5 * d30 + 0.5 * d60
    # Compute blended drift adjustment, clamp, and determine final forecast price
    adjustment = d * horizon_minutes * 0.4
    
    max_adj = 0.004 * L
    if adjustment > max_adj:
        adjustment = max_adj
    elif adjustment < -max_adj:
        adjustment = -max_adj
        
    forecast = L + adjustment
    rounded = round(forecast, 5)
    
    clamped = max(0.00001, min(9999999.99999, rounded))
    return clamped

def read_case(path):
    """
    Reads and parses a case JSON file using a context manager.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def process_inputs():
    """
    Reads every *.in file in the input directory (env MAKEFUN_INPUT_DIR, default /input).
    Computes forecasts and writes <case_id>.out to the output directory
    (env MAKEFUN_OUTPUT_DIR, default /output) as JSON:
    {"forecasts":[{"case":"<case id>","price":<number>}]} followed by a newline.
    """
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    
    if not os.path.exists(input_dir):
        return
        
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".in"):
            in_path = os.path.join(input_dir, filename)
            try:
                data = read_case(in_path)
            except Exception:
                continue
                
            case_id = data.get("case")
            if not case_id:
                case_id = os.path.splitext(filename)[0]
                
            horizon_minutes = data.get("horizon_minutes", 0)
            markets = data.get("markets", [])
            
            forecasts = []
            if markets:
                for market in markets:
                    prices = market.get("prices", [])
                    price = compute_forecast(prices, horizon_minutes)
                    forecasts.append({
                        "case": case_id,
                        "price": price
                    })
            else:
                prices = data.get("prices", [])
                price = compute_forecast(prices, horizon_minutes)
                forecasts.append({
                    "case": case_id,
                    "price": price
                })
                
            out_data = {
                "forecasts": forecasts
            }
            
            out_filename = f"{case_id}.out"
            out_path = os.path.join(out_dir, out_filename)
            
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out_data, f)
                f.write("\n") # Ensure trailing newline in output JSON file

if __name__ == "__main__":
    process_inputs()

# End of module


# BTC Forecast Entry Script

