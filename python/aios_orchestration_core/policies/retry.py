from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3


@dataclass
class RetryState:
    attempts: int = 0

    def increment(self) -> int:
        self.attempts += 1
        return self.attempts

    def exceeded(self, policy: RetryPolicy) -> bool:
        return self.attempts >= policy.max_attempts
