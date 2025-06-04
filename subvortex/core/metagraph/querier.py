import re
from tabulate import tabulate
from dataclasses import asdict

import bittensor.utils.btlogging as btul
import subvortex.core.metagraph.database as scmd


class MetagraphQuerier:
    def __init__(self, config, database: scmd.NeuronDatabase):
        self.config = config
        self.database = database

    async def execute(self):
        filters = self._parse_filters(self.config.filter)
        fields = (
            [f.strip() for f in self.config.fields.split(",") if f.strip()]
            if self.config.fields
            else None
        )

        # Get the neurons
        neurons = await self.database.get_neurons()
        neurons = neurons.values()

        # Convert each Neuron object to a dictionary
        neurons = [asdict(n) for n in neurons]

        # Filtee the neurons
        neurons = self._filter_neurons(neurons, filters) if filters else neurons

        # Sort the neurons
        neurons = self._sort_neurons(neurons, self.config.sort)

        # Display the neurons
        self._display_neurons(neurons, fields)

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

    def _filter_neurons(self, neurons, filters):
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
                        return False  # can't compare non-numeric
                elif op == "in":
                    if actual not in value:
                        return False
                elif op == "not in":
                    if actual in value:
                        return False
            return True

        return [n for n in neurons if match(n)]

    def _sort_neurons(self, neurons, sort_key):
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

        if fields is None:
            fields = sorted(neurons[0].keys())

        rows = [[neuron.get(f, "") for f in fields] for neuron in neurons]
        print(tabulate(rows, headers=fields, tablefmt="fancy_grid"))
