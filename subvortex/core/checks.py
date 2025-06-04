from collections import defaultdict

import bittensor.utils.btlogging as btul


async def check_redis_and_metagraph_consistency():
    btul.logging.info("Checking Redis/Metagraph consistency...")
    successful, total, mismatches = await self.metagraph_checker.run()
    if successful != total:
        btul.logging.warning(
            f"⚠️ {successful}/{total} neurons are consistent between metagraph and Redis."
        )

        # Group mismatches per hotkey
        grouped = defaultdict(list)
        for mismatch in mismatches:
            hotkey = mismatch["hotkey"]
            grouped[hotkey].append(mismatch)

        # Display mismatches for each hotkey
        for hotkey, mismatch_list in grouped.items():
            uid = mismatch_list[0]["uid"]
            fields_str = ", ".join(
                f"{m['field']} (expected={m['expected']}, actual={m['actual']})"
                for m in mismatch_list
            )
            btul.logging.debug(
                f"❌ Mismatch [hotkey={hotkey}, uid={uid}]: {fields_str}"
            )
    else:
        btul.logging.success(
            f"🎉 {successful}/{total} neurons are consistent between metagraph and Redis."
        )
