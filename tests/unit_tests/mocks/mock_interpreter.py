def upgrade_depdencies_side_effect(*args, **kwargs):
    if upgrade_depdencies_side_effect.called:
        # Do nothing on subsequent calls
        return
    else:
        # Raise an error on the first call
        upgrade_depdencies_side_effect.called = True
        raise ValueError("Simulated error")