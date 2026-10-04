import time
import pandas as pd

from .database_service import insert_record


class StreamingSimulator:
    """Read robot CSV records one at a time to simulate a data stream."""

    def __init__(self, csv_path, interval=2):
        self.csv_path = csv_path
        self.interval = interval
        self.data = pd.read_csv(csv_path)
        self.current_index = 0

    def nextDataPoint(self):
        """Return the next record as a one-row DataFrame, or None when exhausted."""
        if self.current_index >= len(self.data):
            return None
        row = self.data.iloc[[self.current_index]].copy()
        self.current_index += 1
        return row

    def next_data_point(self):
        return self.nextDataPoint()

    def reset(self):
        self.current_index = 0

    def start_stream(self, dashboard=None, db_conn=None, max_records=None, sleep=False):
        """Stream records, optionally sending each record to a dashboard/database."""
        count = 0
        while max_records is None or count < max_records:
            point = self.nextDataPoint()
            if point is None:
                break
            record = point.iloc[0]
            if db_conn is not None:
                insert_record(record, conn=db_conn)
            if dashboard is not None:
                if hasattr(dashboard, "update"):
                    dashboard.update(point)
                elif hasattr(dashboard, "plot_data"):
                    dashboard.plot_data(point)
            count += 1
            if sleep:
                time.sleep(self.interval)
        return count
