import bittensor_wallet as btw
import bittensor_wallet.mock as btwm

def get_mock_wallet(coldkey: "btw.Keypair" = None, hotkey: "btw.Keypair" = None):
    wallet = btwm.MockWallet(name="mock_wallet", hotkey="mock", path="/tmp/mock_wallet")

    if not coldkey:
        coldkey = btw.Keypair.create_from_mnemonic(btw.Keypair.generate_mnemonic())
    if not hotkey:
        hotkey = btw.Keypair.create_from_mnemonic(btw.Keypair.generate_mnemonic())

    wallet.set_coldkey(coldkey, encrypt=False, overwrite=True)
    wallet.set_coldkeypub(coldkey, encrypt=False, overwrite=True)
    wallet.set_hotkey(hotkey, encrypt=False, overwrite=True)

    return wallet