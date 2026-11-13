# Greek Day-Ahead Price Predictor (LightGBM)

Trains a LightGBM model that predicts prices on the Greek day-ahead electricity market.
A pretrained model is included, or you can train your own by choosing different training and testing dates.

## Setup

```bash
git clone https://github.com/Dmitsos0/entsoe-day-ahead
cd <repo folder> #the folder where you cloned the repo
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` (same directory as this README) and fill it in:

```
ENTSOE_API_KEY=<your key>
START_DATE_TRAINING=2023-01-10
END_DATE_TRAINING=2025-12-31
START_DATE_TESTING=2026-01-01
END_DATE_TESTING=2026-10-31
```

Replace `<your key>` with a free API key from the [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) (register, then request a key).
Without a key you can still use the pretrained model, but you can't download data beyond what is already included.

The dates control which period the model trains and is tested on.

## Usage

Edit `main.py` (same directory as this README) so it contains one of these calls:

1. `gather()` downloads data for the configured dates.
2. `train()` trains a model on the downloaded data
3. `gather_and_train()` downloads data and trains a model for the configured dates.
4. `predict()` prints the Weighted Absolute Percentage Error (WAPE) and saves a plot of predicted against actual prices as "chart.png" in the same directory as main.py.
5. `train_and_predict()` trains and predicts a model on the downloaded data
6. `do_all()` downloads data for the configured dates and then trains the model and uses it to predict

To use the provided pretrained model, use only `predict()`. Don't run `gather()` or `gather_and_train()`.

then run the main.py file using:
```bash
python main.py
```
## Notes

- All timestamps are UTC.
- Gas prices are shifted by +1 day, so each day-ahead price lines up with the day it affects.
- Missing gas prices are filled with 0.
- The HEnEx scraper depends on the website layout and may break if it changes.
- The pretrained model is tuned for 2026. Other training periods may give lower accuracy.
  Train on at least 3 years of data, and never let the training dates overlap the testing dates, since that could result in unrealistically high accuracy.
- Error can only be measured for days that have already passed, because it needs the actual prices.
  The model can predict future day-ahead prices, but you can't check those predictions until the actual prices are published.
- Please do not run a model on a dataset it wasnt trained for since that could create errors or incorrect predictions
## Data sources

HEnEx and the ENTSO-E Transparency Platform. Check each provider's terms of use.

# License

Licensed under the PolyForm Noncommercial License 1.0.0 (see LICENSE).
Free for personal, educational, research and other noncommercial use,
including running and testing the code. Commercial use needs separate
permission: contact dmitsos19@gmail.com .

This license covers the code only. The ENTSO-E and HEnEx data have their
own terms.