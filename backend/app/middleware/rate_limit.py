from app import limiter

# Apply these decorators to rate-sensitive endpoints
transcript_limit = limiter.limit("60 per minute")
auth_limit       = limiter.limit("10 per minute")
ai_limit         = limiter.limit("20 per hour")
