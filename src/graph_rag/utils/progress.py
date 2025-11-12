"""Progress tracking utilities."""

from typing import Optional

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class ProgressTracker:
    """Progress tracker for long-running operations."""

    def __init__(self, total: int, desc: str = "Processing"):
        """Initialize progress tracker.

        Args:
            total: Total number of items
            desc: Description string
        """
        self.total = total
        self.desc = desc
        self.current = 0
        self.pbar = None

        if TQDM_AVAILABLE:
            self.pbar = tqdm(total=total, desc=desc, unit="item")

    def update(self, n: int = 1):
        """Update progress.

        Args:
            n: Number of items completed
        """
        self.current += n
        if self.pbar:
            self.pbar.update(n)
        else:
            # Fallback: print progress
            if self.current % max(1, self.total // 20) == 0 or self.current == self.total:
                percent = (self.current / self.total) * 100
                print(f"{self.desc}: {self.current}/{self.total} ({percent:.1f}%)")

    def close(self):
        """Close progress tracker."""
        if self.pbar:
            self.pbar.close()
        elif self.current == self.total:
            print(f"{self.desc}: Complete ({self.current}/{self.total})")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

