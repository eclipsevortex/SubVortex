import subvortex.validator.core.challenger.challenges.bittensor.challenge_neuron_info as svccni

CHALLENGES = {"bittensor": [(svccni.create_challenge, svccni.execute_challenge)]}
