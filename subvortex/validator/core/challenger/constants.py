# Number of seconds to build a block
BLOCK_BUILD_TIME = 12

# After this many blocks pass, a block can be considered final
DYNAMIC_BLOCK_FINALIZATION_NUMBER = 3

# Number of historic blocks a lite node has (300 blocks in total)
LITE_NODE_BLOCK_UPPER_LIMIT = 10
LITE_NODE_BLOCK_LOWER_LIMIT = 250

TOP_X_MINERS = 3

# Failure rewards for each metrics
AVAILABILITY_FAILURE_REWARD = 0.0
LATENCY_FAILURE_REWARD = 0.0
DISTRIBUTION_FAILURE_REWARD = 0.0
RELIABILLITY_FAILURE_REWARD = 0.0
PERFORMANCE_FAILURE_REWARD = 0.0

# Performance settings
PERFORMANCE_REWARD_EXPONENT = 0.7
PERFORMANCE_PENALTY_FACTOR = 0.7