import matplotlib.pyplot as plt


class RobotDashboard:
    """Small reusable dashboard helper for streaming demonstrations."""

    def __init__(self):
        self.history = []

    def update(self, data):
        self.history.append(data.copy())

    def plot_data(self, data):
        self.update(data)

    def show(self):
        if not self.history:
            return
        import pandas as pd
        df = pd.concat(self.history, ignore_index=True)
        axes = [c for c in df.columns if str(c).startswith("Axis #")]
        if axes:
            df[axes].plot(figsize=(12, 5))
            plt.title("Robot Axis Current")
            plt.xlabel("Stream record")
            plt.ylabel("Current")
            plt.tight_layout()
            plt.show()
