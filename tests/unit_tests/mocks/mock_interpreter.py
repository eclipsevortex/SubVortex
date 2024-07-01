def install_depdencies_side_effect(*args, **kwargs):
    if install_depdencies_side_effect.called:
        # Do nothing on subsequent calls
        return
    else:
        # Raise an error on the first call
        install_depdencies_side_effect.called = True
        raise ValueError("Simulated error")