#!/usr/bin/env python3
"""
BTC Price Forecasting module.
Forecasts BTC price ahead (e.g. 4 hours ahead) based on recent price trends and drift calculations.
"""
import os
import json

def compute_forecast(prices, horizon_minutes):
    """Compute the forecasted price given historical prices and horizon minutes."""
    if not prices:
        return 0.0
    
    L = prices[-1]
    length = len(prices)
    
    if length > 61:
        d60 = (L - prices[-61]) / 60.0
    else:
        d60 = 0.0
        
    if length > 31:
        d30 = (L - prices[-31]) / 30.0
    else:
        d30 = 0.0
        
    # Blended per-minute drift based on 30-minute and 60-minute windows
    d = 0.5 * d30 + 0.5 * d60
    adjustment = d * horizon_minutes * 0.4
    
    max_adj = 0.004 * L
    if adjustment > max_adj:
        adjustment = max_adj
    elif adjustment < -max_adj:
        adjustment = -max_adj
        
    forecast = L + adjustment
    forecast = round(forecast, 5)
    forecast = max(0.00001, min(9999999.99999, forecast))
    return forecast

def read_case(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def process_inputs():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    
    if not os.path.isdir(input_dir):
        return
        
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".in"):
            input_path = os.path.join(input_dir, filename)
            try:
                data = read_case(input_path)
            except Exception:
                continue
                
            case_id = data.get("case")
            if not case_id:
                case_id = os.path.splitext(filename)[0]
                
            horizon_minutes = data.get("horizon_minutes", 0)
            markets = data.get("markets", [])
            
            forecasts = []
            for market in markets:
                prices = market.get("prices", [])
                forecast_price = compute_forecast(prices, horizon_minutes)
                forecasts.append({
                    "case": case_id,
                    "price": forecast_price
                })
                
            output_data = {
                "forecasts": forecasts
            }
            
            output_path = os.path.join(out_dir, f"{case_id}.out")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")  # Write trailing newline to output file

if __name__ == "__main__":
    process_inputs()

# End of module
# EOF
