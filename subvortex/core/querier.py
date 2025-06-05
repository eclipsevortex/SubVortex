import re
import shutil
from itertools import islice
from tabulate import tabulate
from dataclasses import asdict

import bittensor.utils.btlogging as btul
import subvortex.core.metagraph.database as scmd

MAX_COLUMN_WIDTH = 20


class Querier:
    def __init__(self, config):
        self.config = config

    async def execute(self, data):
        filters = self._parse_filters(self.config.filter)
        fields = (
            [f.strip() for f in self.config.fields.split(",") if f.strip()]
            if self.config.fields
            else None
        )

        # Convert each item to a dictionary
        items = [asdict(n) for n in data]

        # Filtee the neurons
        items = self._filter_items(items, filters) if filters else items

        # Sort the neurons
        items = self._sort_items(items, self.config.sort)

        # Display the neurons
        self._display_neurons(items, fields)

    def _parse_filters(self, filter_args):
        filter_ops = []
        for arg in filter_args:
            # Matches key >= value
            if match := re.match(r"(\w+)\s*(>=|<=|!=|=|<|>)\s*(.+)", arg):
                key, op, value = match.groups()
                if op == "=":
                    op = "=="
                filter_ops.append((key, op, value))
            elif match := re.match(r"(\w+)\s+not\s+in\s+(.+)", arg):
                filter_ops.append((match.group(1), "not in", match.group(2).split(",")))
            elif match := re.match(r"(\w+)\s+in\s+(.+)", arg):
                filter_ops.append((match.group(1), "in", match.group(2).split(",")))
            else:
                raise ValueError(f"Unsupported filter format: {arg}")
        return filter_ops

    def _filter_items(self, neurons, filters):
        def match(neuron):
            for key, op, value in filters:
                actual = neuron.get(key)
                if actual is None:
                    return False

                # Handle numeric comparisons
                if op in {"<", ">", "<=", ">=", "==", "!="}:
                    try:
                        actual_num = float(actual)
                        value_num = float(value)
                        if not eval(f"{actual_num} {op} {value_num}"):
                            return False
                    except ValueError:
                        if op in {"==", "!="}:
                            # fallback to string comparison
                            actual_str = str(actual)
                            value_str = str(value)
                            if op == "==" and actual_str != value_str:
                                return False
                            elif op == "!=" and actual_str == value_str:
                                return False
                        else:
                            return False
                elif op == "in":
                    if actual not in value:
                        return False
                elif op == "not in":
                    if actual in value:
                        return False
            return True

        return [n for n in neurons if match(n)]

    def _sort_items(self, neurons, sort_key):
        if not sort_key:
            return neurons

        descending = False
        if sort_key.startswith("-"):
            descending = True
            sort_key = sort_key[1:]

        try:
            return sorted(
                neurons, key=lambda n: float(n.get(sort_key, 0)), reverse=descending
            )
        except ValueError:
            return sorted(
                neurons, key=lambda n: str(n.get(sort_key, "")), reverse=descending
            )

    def _display_neurons(self, neurons, fields=None):
        if not neurons:
            btul.logging.warning("No matching neurons found.")
            return

        user_provided_fields = fields is not None

        # Get the list of columns
        available_fields = sorted(neurons[0].keys())
        print(f"📋 Available columns: {', '.join(available_fields)}\n")

        if not user_provided_fields:
            # Terminal width limit only if fields aren't provided
            term_width = shutil.get_terminal_size((120, 40)).columns
            max_columns = term_width // (MAX_COLUMN_WIDTH + 3)

            if len(available_fields) > max_columns:
                print(
                    f"🔍 Displaying only first {max_columns} fields to fit terminal width"
                )
                fields = available_fields[:max_columns]

        def maybe_truncate(val, maxlen=MAX_COLUMN_WIDTH):
            val = str(val)
            if not user_provided_fields and len(val) > maxlen:
                return val[: maxlen - 3] + "..."
            return val

        def chunked(iterable, size):
            it = iter(iterable)
            return iter(lambda: list(islice(it, size)), [])

        rows = [
            [maybe_truncate(neuron.get(f, "")) for f in fields] for neuron in neurons
        ]

        for page_number, chunk in enumerate(
            chunked(rows, self.config.page_size), start=1
        ):
            print(f"\n📄 Page {page_number} (showing {len(chunk)} neurons):\n")
            print(tabulate(chunk, headers=fields, tablefmt="fancy_grid"))
            if page_number * self.config.page_size >= len(neurons):
                break
            input("Press Enter to continue...")
