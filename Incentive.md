# Introduction

We want to assure the ownership of the registered subtensor by the miner and measure its performance against others.

To do so, the validator will send for now 2 synapse
- Subtensor - the synapse is sent to the miner to gather all the information about the subtensor and the machine it is host to such as ip, geolocalisation, bandwidth, etc
- Challenge - the synapse is sent to the miner to check the 

# Synapse Subtensor
This synapse has for objective to gather any information about the subtensor and the host in order to compute some metrics that will be used to compute the final reward.

The synapse will gather the following informations
- ip - ip of the subtensor
- download - number of B/s to complete a download task
- upload - number of B/s to complete a upload task
- ping - number of milliseconds to answer to a ping
- country - country of the subtensor host
- region - region of the subtensor host
- city - city of the subtensor host

From these information, few metrics will be computed
- Ownership - we want to be sure the miner and the referenced subtensor (via --subtensor.chain_endpoint) are hosted on the same machine to prove ownership
- Unicity - we want to be sure a subtensor is referenced to only one miner. We want to avoid a subtensor to be referenced by multiple miners.
- Diversity - We want to encourage a coldkey to own subtensor in multiple geolocalisation. 

Potential issues
- Prevent a miner to reference a subtensor its does not own
- Prevent a miner to lie on its characteristics


# Synapse Challenge
This synapse has for objective to challenge the subtensor.




RD Miner - RD subtensor => same ip ok 
RD Miner - JD subtensor => different ip (miner ip can not be changed as it is used to create the axon)