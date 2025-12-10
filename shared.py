from pathlib import Path

import pandas as pd

# Load data
app_dir = Path(__file__).parent
aggression_df = pd.read_csv(app_dir / "quality_aggression.csv")
power_vs_expected_df = pd.read_csv(app_dir / "power_vs_expected.csv")
radial_profile_df = pd.read_csv(app_dir / "hitter_radial_profile.csv")
