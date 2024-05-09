SubVortex's incentive mechanism will score miners based on multiple criteria of their subtensor node:

- **Availability** - Subtensor nodes must be reliable to ensure good uptime.
- **Latency** - Subtensor nodes must be efficient to ensure good performance.
- **Reliability** and Stability - Subtensor nodes must be efficient to ensure good service quality.
- **Global distribution** - Subtensor nodes must be worldwide to ensure a good reach.

The final score used to set the weight is an average of all these scores and will replace 10% of the weight of the previous weights.

To better understand the following, you need to grasp a few concepts:

- A miner is flagged as suspicious if it appears in the suspicious UID file. A penalty factor may be provided to adjust the scores accordingly.
- A miner is considered verified if both the miner and subtensor are operational and accessible.

<br />

# Availability

This reward incentivizes miners to maintain high levels of uptime and accessibility.

To assign a score for each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by the success of getting that block.

The score will be computed based on these rules:

- If the miner is flagged as suspicious with no penalise factor, the score will be 0.
- If the miner is flagged as suspicious with penalise factor, the score will be the penalise factor.
- If the miner is not verified, the score will be 0.
- If there are more than one miner on the same IP, the score will be 0.
- Otherwise, the score will be 1.

<br />

# Latency

This reward incentivizes miners to low-latency services and minimizes response times.

To assign a score to each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by the time taken to process that request, using a normalized method as part of the reward system.

The validator can be in a different country than the miner, so we will incorporate a distance-based weighting factor into the scoring formula.

The score will be computed based on these rules:

- If the miner is flagged as suspicious with no penalise factor, the score will be 0.
- If the miner is flagged as suspicious with penalise factor, the score will be the penalise factor.
- If the miner is not verified, the score will be 0.
- If there are more than one miner on the same IP, the score will be 0.
- Otherwise, the score will be computed based on the time taken to request directly the subtensor, adding a tolerance based on the distance between validator/miner and normalise it against other miners. So the best miner will receive 1 and the worst will receive 0.

<br />

# Reliability and Stability

This reward incentivizes miners to have high levels of reliability and minimize the occurrence and impact of failures.

To assign a score to each miner, we will establish a connection with the subtensor and retrieve the current block. The score will be determined by computing the ratio of successes/attempts, using a normalized method as part of the reward system.

The score will be computed based on these rules:

- If the miner is flagged as suspicious with no penalise factor, the score will be 0.
- If the miner is flagged as suspicious with penalise factor, the score will be the penalise factor.
- Otherwise the score will be # of attemps / # of success normalised with wilson.

<br />

# Global Distribution

This reward incentivizes miners to effectively distribute subtensors across different geographical locations to optimize performance and reduce latency for a better subnet experience.

The score will be computed based on these rules:

- If the miner is flagged as suspicious with no penalise factor, the score will be 0.
- If the miner is flagged as suspicious with penalise factor, the score will be the penalise factor.
- If the miner is not verified, the score will be 0.
- If there are more than one miner on the same IP, the score will be 0.
- Otherwise, the score will be 1 / # of miners in that location (your miner included)

<br />

# Final score

The final score is the score for the current challenge. It will be computed as the weighted average of the scores above.

The weight for each score will be as follows:

- Availability: Weight will be **3** if the miner's subtensor is synchronized, and **1** otherwise.
- Latency: Weight will be **1**.
- Reliability: Weight will be **1**.
- Distribution: Weight will be **1**.

So, the final formula will be calculated using the following expression

```
final score = (
        (availability weight * availability score) +
        (latency weight * latency score) +
        (reliability weight * reliability score) +
        (distribution weight * distribution score)
    ) / (
        availability weight +
        latency weight +
        reliability weight +
        distribution weight
    )
```

<br />

# Average Moving Score

The average moving score represents the score for all previous challenges. It is calculated by applying a weighting factor (alpha) to the current average moving score and the new score.

So, the final formula will be calculated using the following expression

```
average moving score = 0.1 * score * 0.9 previous average moving score
```

The average moving score can be overrided with

- 0 if the miner is suspicious with no penalise factor provided
- penalise factor if the miner is suspicious with penalise factor provided
