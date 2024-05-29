import bittensor as bt


class SubVortexMetagraph(bt.metagraph):
    def get_validators(self, weights_min_stake: int = 0):
        """
        Return the list of active validator.
        An active validator is a validator staking the minimum required
        """
        validators = []

        for neuron in self.neurons:
            stake = self.S[neuron.uid]
            if stake < weights_min_stake:
                # Skip any validator that has not enough stake to set weight
                continue

            validator = (
                neuron.uid,
                neuron.hotkey,
                stake,
            )
            validators.append(validator)

        return validators
